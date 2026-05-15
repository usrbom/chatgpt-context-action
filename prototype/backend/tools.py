from __future__ import annotations

import json
import uuid
from datetime import datetime

import claude_search
import db
import mock_api


def get_recommendations(
    user_id: str,
    location: str,
    date: str,
    time_bucket: str,
    party_size: int,
    cuisine: str | None = None,
) -> dict:
    history_records = db.get_history(user_id, location, time_bucket, cuisine)
    history_context_applies = len(history_records) > 0
    preference_signals = db.get_preference_signals(user_id) or {}
    history_names = [r["venue_name"] for r in history_records]

    bucket_to_time = {
        "morning": "09:00",
        "afternoon": "13:00",
        "evening": "19:00",
        "late_night": "22:00",
    }
    search_time = bucket_to_time.get(time_bucket, "19:00")

    search_results = claude_search.search_restaurants(
        location, date, search_time, party_size, cuisine,
        history_venue_names=history_names,
    )
    if not search_results:
        search_results = mock_api.search_restaurants(location, date, search_time, party_size, cuisine)

    # Re-rank: venues in history first (by visit_count → last_visited), then rest by rating
    history_names = {r["venue_name"]: r for r in history_records}
    in_history = []
    not_in_history = []
    for venue in search_results:
        if venue["venue_name"] in history_names:
            rec = history_names[venue["venue_name"]]
            in_history.append((venue, rec["visit_count"], rec["last_visited"]))
        else:
            not_in_history.append(venue)

    in_history.sort(key=lambda x: (-x[1], x[2]), reverse=False)
    in_history.sort(key=lambda x: (-x[1], [-ord(c) for c in x[2]]))
    ranked = [v for v, _, _ in in_history] + not_in_history

    top = ranked[:5]

    return {
        "history_context_applies": history_context_applies,
        "restaurant_history": [
            {
                "record_id": r["record_id"],
                "venue_name": r["venue_name"],
                "location_bucket": r["location_bucket"],
                "cuisine": r["cuisine"],
                "typical_time_bucket": r["typical_time_bucket"],
                "visit_count": r["visit_count"],
                "last_visited": r["last_visited"],
                "party_size_avg": r["party_size_avg"],
            }
            for r in history_records
        ],
        "preference_signals": preference_signals,
        "recommendations": top,
    }


def book_dining(
    user_id: str,
    venue_id: str,
    venue_name: str,
    date: str,
    time: str,
    party_size: int,
    counterparty_name: str,
    counterparty_phone: str,
    session_id: str = "",
) -> dict:
    result = mock_api.book_restaurant(venue_id, venue_name, date, time, party_size, counterparty_name, counterparty_phone)

    if result["booking_confirmed"]:
        venue = mock_api.get_venue_by_id(venue_id)
        event = {
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "dining",
            "action": "book_restaurant",
            "payload": {
                "title": venue_name,
                "location": {"name": venue["location_bucket"] if venue else "", "lat": 0, "lon": 0},
                "time": f"{date}T{time}:00Z",
                "counterparty": venue_name,
                "amount": venue["estimated_cost_per_person"] if venue else 0,
                "category_tags": [venue["cuisine"] if venue else ""],
            },
            "outcome": "confirmed",
            "session_id": session_id or str(uuid.uuid4()),
        }
        db.log_raw_event(event)
        db.recompute_derived(user_id)

    return result


def show_patterns(user_id: str) -> dict:
    history = db.get_all_history(user_id)
    signals = db.get_preference_signals(user_id) or {}
    return {
        "restaurant_history": history,
        "preference_signals": signals,
    }


def forget_me(user_id: str) -> dict:
    removed = db.delete_user_data(user_id)
    return {
        "deleted": True,
        "records_removed": removed,
        "message": f"All behavioral data for your account has been permanently deleted ({removed} records removed).",
    }
