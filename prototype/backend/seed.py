"""Seed the SQLite store with user history from user_history.json."""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import db

USER_HISTORY_PATH = Path(__file__).parent.parent.parent / "appendix" / "eval" / "user_history.json"


def main() -> None:
    db.init_db()

    with open(USER_HISTORY_PATH) as f:
        data = json.load(f)

    user_id = data["meta"]["user_id"]

    # Shift last_visited dates to be relative to today so the 90-day history
    # window never expires, regardless of when the repo was cloned.
    reference_date = date.fromisoformat(data["meta"]["computed_at"][:10])
    shift = date.today() - reference_date
    for record in data["restaurant_history"]:
        original = date.fromisoformat(record["last_visited"])
        record["last_visited"] = (original + shift).isoformat()
    data["preference_signals"]["computed_at"] = date.today().isoformat() + "T00:00:00Z"

    # Clear existing data for demo user
    db.delete_user_data(user_id)

    # Insert restaurant history records directly
    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    for record in data["restaurant_history"]:
        conn.execute(
            """INSERT OR REPLACE INTO restaurant_history
               (record_id, user_id, venue_name, venue_id, location_bucket, cuisine,
                typical_time_bucket, typical_day_type, visit_count, last_visited,
                party_size_avg, counterparty_type, window_days)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record["record_id"],
                record["user_id"],
                record["venue_name"],
                record.get("venue_id"),
                record["location_bucket"],
                record["cuisine"],
                record["typical_time_bucket"],
                record.get("typical_day_type"),
                record["visit_count"],
                record["last_visited"],
                record["party_size_avg"],
                record.get("counterparty_type"),
                record.get("window_days", 90),
            ),
        )

    # Insert preference signals
    signals = data["preference_signals"]
    conn.execute(
        "INSERT OR REPLACE INTO preference_signals (user_id, computed_at, window_days, data) VALUES (?, ?, ?, ?)",
        (user_id, signals["computed_at"], signals["window_days"], json.dumps(signals)),
    )
    conn.commit()
    conn.close()

    count = len(data["restaurant_history"])
    print(f"Seeded {count} restaurant history records for {user_id}")
    print(f"Database: {db.DB_PATH}")


if __name__ == "__main__":
    main()
