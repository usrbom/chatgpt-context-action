import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS raw_events (
                event_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                action TEXT NOT NULL,
                payload TEXT NOT NULL,
                outcome TEXT NOT NULL,
                session_id TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS restaurant_history (
                record_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                venue_name TEXT NOT NULL,
                venue_id TEXT,
                location_bucket TEXT NOT NULL,
                cuisine TEXT NOT NULL,
                typical_time_bucket TEXT NOT NULL,
                typical_day_type TEXT,
                visit_count INTEGER NOT NULL,
                last_visited TEXT NOT NULL,
                party_size_avg REAL NOT NULL,
                counterparty_type TEXT,
                window_days INTEGER NOT NULL DEFAULT 90,
                PRIMARY KEY (record_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS preference_signals (
                user_id TEXT PRIMARY KEY,
                computed_at TEXT NOT NULL,
                window_days INTEGER NOT NULL DEFAULT 90,
                data TEXT NOT NULL
            );
        """)


def get_history(user_id: str, location: str, time_bucket: str, cuisine: str | None) -> list[dict]:
    with get_conn() as conn:
        if cuisine:
            rows = conn.execute(
                """SELECT * FROM restaurant_history
                   WHERE user_id = ? AND location_bucket = ? AND typical_time_bucket = ? AND cuisine = ?
                   ORDER BY visit_count DESC, last_visited DESC""",
                (user_id, location, time_bucket, cuisine),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT * FROM restaurant_history
                   WHERE user_id = ? AND location_bucket = ? AND typical_time_bucket = ?
                   ORDER BY visit_count DESC, last_visited DESC""",
                (user_id, location, time_bucket),
            ).fetchall()
    return [dict(r) for r in rows]


def get_preference_signals(user_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT data FROM preference_signals WHERE user_id = ?", (user_id,)
        ).fetchone()
    if row:
        return json.loads(row["data"])
    return None


def get_all_history(user_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM restaurant_history WHERE user_id = ? ORDER BY visit_count DESC, last_visited DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def log_raw_event(event: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO raw_events
               (event_id, user_id, timestamp, category, action, payload, outcome, session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event["event_id"],
                event["user_id"],
                event["timestamp"],
                event["category"],
                event["action"],
                json.dumps(event["payload"]),
                event["outcome"],
                event["session_id"],
            ),
        )


def recompute_derived(user_id: str) -> None:
    """Recompute restaurant_history and preference_signals from raw_events."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM raw_events WHERE user_id = ? AND outcome = 'confirmed'",
            (user_id,),
        ).fetchall()

    if not rows:
        return

    venue_map: dict[str, dict] = {}
    for row in rows:
        payload = json.loads(row["payload"])
        venue = payload.get("counterparty", "")
        if not venue:
            continue
        ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        hour = ts.hour
        if 6 <= hour < 12:
            tb = "morning"
        elif 12 <= hour < 17:
            tb = "afternoon"
        elif 17 <= hour < 22:
            tb = "evening"
        else:
            tb = "late_night"
        dow = ts.weekday()
        day_type = "weekday" if dow < 5 else "weekend"

        if venue not in venue_map:
            venue_map[venue] = {
                "venue_name": venue,
                "location_bucket": payload.get("location", {}).get("name", ""),
                "cuisine": payload.get("category_tags", [""])[0] if payload.get("category_tags") else "",
                "time_buckets": [],
                "day_types": [],
                "visit_count": 0,
                "last_visited": "",
                "party_sizes": [],
            }
        venue_map[venue]["visit_count"] += 1
        venue_map[venue]["time_buckets"].append(tb)
        venue_map[venue]["day_types"].append(day_type)
        date_str = ts.strftime("%Y-%m-%d")
        if date_str > venue_map[venue]["last_visited"]:
            venue_map[venue]["last_visited"] = date_str
        venue_map[venue]["party_sizes"].append(payload.get("amount", 1))

    with get_conn() as conn:
        for i, (venue, data) in enumerate(venue_map.items(), start=1):
            from collections import Counter
            modal_tb = Counter(data["time_buckets"]).most_common(1)[0][0]
            dt_counts = Counter(data["day_types"])
            if dt_counts.get("weekday", 0) == dt_counts.get("weekend", 0):
                modal_dt = None
            else:
                modal_dt = dt_counts.most_common(1)[0][0]
            avg_party = round(sum(data["party_sizes"]) / len(data["party_sizes"]), 1)
            conn.execute(
                """INSERT OR REPLACE INTO restaurant_history
                   (record_id, user_id, venue_name, venue_id, location_bucket, cuisine,
                    typical_time_bucket, typical_day_type, visit_count, last_visited,
                    party_size_avg, counterparty_type, window_days)
                   VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, NULL, 90)""",
                (
                    f"RH_NEW_{i:03d}",
                    user_id,
                    data["venue_name"],
                    data["location_bucket"],
                    data["cuisine"],
                    modal_tb,
                    modal_dt,
                    data["visit_count"],
                    data["last_visited"],
                    avg_party,
                ),
            )

        # Rebuild preference_signals
        all_rows = conn.execute(
            "SELECT * FROM restaurant_history WHERE user_id = ?", (user_id,)
        ).fetchall()

        cuisine_counts: dict[str, int] = {}
        neighborhood_counts: dict[str, int] = {}
        time_counts: dict[str, int] = {}
        day_counts: dict[str, int] = {}

        for r in all_rows:
            cuisine_counts[r["cuisine"]] = cuisine_counts.get(r["cuisine"], 0) + r["visit_count"]
            neighborhood_counts[r["location_bucket"]] = neighborhood_counts.get(r["location_bucket"], 0) + r["visit_count"]
            time_counts[r["typical_time_bucket"]] = time_counts.get(r["typical_time_bucket"], 0) + r["visit_count"]
            if r["typical_day_type"]:
                day_counts[r["typical_day_type"]] = day_counts.get(r["typical_day_type"], 0) + r["visit_count"]

        signals = {
            "computed_at": datetime.utcnow().isoformat() + "Z",
            "window_days": 90,
            "cuisines": [
                {"cuisine": c, "visit_count": v, "rank": i + 1}
                for i, (c, v) in enumerate(sorted(cuisine_counts.items(), key=lambda x: -x[1]))
            ],
            "neighborhoods": [
                {"location_bucket": n, "visit_count": v, "rank": i + 1}
                for i, (n, v) in enumerate(sorted(neighborhood_counts.items(), key=lambda x: -x[1]))
            ],
            "time_preferences": [
                {"time_bucket": t, "visit_count": v, "rank": i + 1}
                for i, (t, v) in enumerate(sorted(time_counts.items(), key=lambda x: -x[1]))
            ],
            "day_preferences": [
                {"day_type": d, "visit_count": v, "rank": i + 1}
                for i, (d, v) in enumerate(sorted(day_counts.items(), key=lambda x: -x[1]))
            ],
        }
        conn.execute(
            "INSERT OR REPLACE INTO preference_signals (user_id, computed_at, window_days, data) VALUES (?, ?, ?, ?)",
            (user_id, signals["computed_at"], 90, json.dumps(signals)),
        )


def delete_user_data(user_id: str) -> int:
    with get_conn() as conn:
        r1 = conn.execute("DELETE FROM raw_events WHERE user_id = ?", (user_id,)).rowcount
        r2 = conn.execute("DELETE FROM restaurant_history WHERE user_id = ?", (user_id,)).rowcount
        r3 = conn.execute("DELETE FROM preference_signals WHERE user_id = ?", (user_id,)).rowcount
    return r1 + r2 + r3
