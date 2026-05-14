#!/usr/bin/env python3
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "appendix", "eval", "user_history.json"
)


def seed():
    db.init_db()

    with open(HISTORY_FILE) as f:
        data = json.load(f)

    user_id = data["meta"]["user_id"]
    db.load_history_records(data["restaurant_history"])
    db.load_preference_signals(user_id, data["preference_signals"])

    print(f"Seeded {len(data['restaurant_history'])} restaurant history records for {user_id}")
    cuisines = len(data["preference_signals"].get("cuisines", []))
    neighborhoods = len(data["preference_signals"].get("neighborhoods", []))
    print(f"Seeded preference signals: {cuisines} cuisines, {neighborhoods} neighborhoods")
    print("Done.")


if __name__ == "__main__":
    seed()
