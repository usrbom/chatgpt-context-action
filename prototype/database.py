import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "booking.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS restaurant_history (
                record_id TEXT PRIMARY KEY,
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
                window_days INTEGER NOT NULL DEFAULT 90
            );

            CREATE TABLE IF NOT EXISTS preference_signals (
                user_id TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                value TEXT NOT NULL,
                visit_count INTEGER NOT NULL,
                rank INTEGER NOT NULL,
                computed_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, signal_type, value)
            );

            CREATE TABLE IF NOT EXISTS raw_events (
                event_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'dining',
                action TEXT NOT NULL DEFAULT 'book_restaurant',
                payload TEXT NOT NULL,
                outcome TEXT NOT NULL,
                session_id TEXT NOT NULL
            );
        """)


def load_history_records(records: list):
    with get_conn() as conn:
        for r in records:
            conn.execute("""
                INSERT OR REPLACE INTO restaurant_history
                (record_id, user_id, venue_name, venue_id, location_bucket, cuisine,
                 typical_time_bucket, typical_day_type, visit_count, last_visited,
                 party_size_avg, counterparty_type, window_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["record_id"], r["user_id"], r["venue_name"], r.get("venue_id"),
                r["location_bucket"], r["cuisine"], r["typical_time_bucket"],
                r.get("typical_day_type"), r["visit_count"], r["last_visited"],
                r["party_size_avg"], r.get("counterparty_type"), r.get("window_days", 90)
            ))


def load_preference_signals(user_id: str, signals: dict):
    computed_at = signals.get("computed_at", "")
    with get_conn() as conn:
        for s in signals.get("cuisines", []):
            conn.execute(
                "INSERT OR REPLACE INTO preference_signals (user_id, signal_type, value, visit_count, rank, computed_at) VALUES (?, 'cuisine', ?, ?, ?, ?)",
                (user_id, s["cuisine"], s["visit_count"], s["rank"], computed_at)
            )
        for s in signals.get("neighborhoods", []):
            conn.execute(
                "INSERT OR REPLACE INTO preference_signals (user_id, signal_type, value, visit_count, rank, computed_at) VALUES (?, 'neighborhood', ?, ?, ?, ?)",
                (user_id, s["location_bucket"], s["visit_count"], s["rank"], computed_at)
            )
        for s in signals.get("time_preferences", []):
            conn.execute(
                "INSERT OR REPLACE INTO preference_signals (user_id, signal_type, value, visit_count, rank, computed_at) VALUES (?, 'time_bucket', ?, ?, ?, ?)",
                (user_id, s["time_bucket"], s["visit_count"], s["rank"], computed_at)
            )
        for s in signals.get("day_preferences", []):
            conn.execute(
                "INSERT OR REPLACE INTO preference_signals (user_id, signal_type, value, visit_count, rank, computed_at) VALUES (?, 'day_type', ?, ?, ?, ?)",
                (user_id, s["day_type"], s["visit_count"], s["rank"], computed_at)
            )


def get_restaurant_history(user_id: str, location: str, time_bucket: str, cuisine: str = None) -> list:
    with get_conn() as conn:
        query = """
            SELECT * FROM restaurant_history
            WHERE user_id = ? AND location_bucket = ? AND typical_time_bucket = ?
        """
        params = [user_id, location, time_bucket]
        if cuisine:
            query += " AND cuisine = ?"
            params.append(cuisine)
        query += " ORDER BY visit_count DESC, last_visited DESC"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_preference_signals(user_id: str) -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT signal_type, value, visit_count, rank FROM preference_signals WHERE user_id = ? ORDER BY rank",
            (user_id,)
        ).fetchall()

    result = {"cuisines": [], "neighborhoods": [], "time_preferences": [], "day_preferences": []}
    for row in rows:
        r = dict(row)
        if r["signal_type"] == "cuisine":
            result["cuisines"].append({"cuisine": r["value"], "visit_count": r["visit_count"], "rank": r["rank"]})
        elif r["signal_type"] == "neighborhood":
            result["neighborhoods"].append({"location_bucket": r["value"], "visit_count": r["visit_count"], "rank": r["rank"]})
        elif r["signal_type"] == "time_bucket":
            result["time_preferences"].append({"time_bucket": r["value"], "visit_count": r["visit_count"], "rank": r["rank"]})
        elif r["signal_type"] == "day_type":
            result["day_preferences"].append({"day_type": r["value"], "visit_count": r["visit_count"], "rank": r["rank"]})
    return result


def get_all_history(user_id: str) -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM restaurant_history WHERE user_id = ? ORDER BY visit_count DESC",
            (user_id,)
        ).fetchall()
    history = [dict(r) for r in rows]
    signals = get_preference_signals(user_id)
    return {"restaurant_history": history, "preference_signals": signals}


def log_event(event: dict):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO raw_events (event_id, user_id, timestamp, category, action, payload, outcome, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event["event_id"], event["user_id"], event["timestamp"],
            event.get("category", "dining"), event.get("action", "book_restaurant"),
            json.dumps(event.get("payload", {})), event["outcome"], event["session_id"]
        ))


def delete_user_history(user_id: str) -> int:
    with get_conn() as conn:
        r1 = conn.execute("DELETE FROM restaurant_history WHERE user_id = ?", (user_id,))
        r2 = conn.execute("DELETE FROM preference_signals WHERE user_id = ?", (user_id,))
        r3 = conn.execute("DELETE FROM raw_events WHERE user_id = ?", (user_id,))
        return r1.rowcount + r2.rowcount + r3.rowcount


def count_events(user_id: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as c FROM raw_events WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["c"]
