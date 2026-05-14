import uuid
from datetime import datetime
import database as db
import mock_api


def get_recommendations(
    location: str, date: str, time_bucket: str, party_size: int,
    cuisine: str = None, user_id: str = "demo_user_01"
) -> dict:
    history_records = db.get_restaurant_history(user_id, location, time_bucket, cuisine)
    history_context_applies = len(history_records) > 0

    restaurants = mock_api.search_restaurants(location, time_bucket, cuisine)
    if not restaurants:
        return {
            "history_context_applies": False,
            "restaurants": [],
            "message": f"No restaurants found in {location} for {time_bucket}."
        }

    history_names = {r["venue_name"] for r in history_records}
    history_lookup = {r["venue_name"]: r for r in history_records}

    in_history = [r for r in restaurants if r["venue_name"] in history_names]
    not_in_history = [r for r in restaurants if r["venue_name"] not in history_names]

    # Stable two-pass sort: last_visited desc, then visit_count desc (more visits = higher rank)
    in_history.sort(key=lambda r: history_lookup[r["venue_name"]]["last_visited"], reverse=True)
    in_history.sort(key=lambda r: history_lookup[r["venue_name"]]["visit_count"], reverse=True)
    not_in_history.sort(key=lambda r: r["rating"], reverse=True)

    ranked = (in_history + not_in_history)[:5]

    return {
        "history_context_applies": history_context_applies,
        "restaurants": ranked
    }


def book_dining(
    venue_id: str, venue_name: str, date: str, time: str, party_size: int,
    counterparty_name: str, counterparty_phone: str,
    user_id: str = "demo_user_01", session_id: str = "default"
) -> dict:
    result = mock_api.make_booking(venue_id, date, time, party_size, counterparty_name, counterparty_phone)

    if result["booking_confirmed"]:
        restaurant = mock_api._venue_index.get(venue_id, {})
        event = {
            "event_id": str(uuid.uuid4()),
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "dining",
            "action": "book_restaurant",
            "payload": {
                "title": venue_name,
                "location": {"name": restaurant.get("location_bucket", "")},
                "time": f"{date}T{time}:00Z",
                "counterparty": venue_name,
                "amount": restaurant.get("estimated_cost_per_person", 0),
                "category_tags": [restaurant.get("cuisine", "")]
            },
            "outcome": "confirmed",
            "session_id": session_id
        }
        db.log_event(event)
        result["event_id"] = event["event_id"]

    return result


def show_patterns(user_id: str) -> dict:
    data = db.get_all_history(user_id)
    if not data["restaurant_history"]:
        return {"message": "No behavioral history on record.", "restaurant_history": [], "preference_signals": {}}
    return data


def forget_me(user_id: str) -> dict:
    removed = db.delete_user_history(user_id)
    return {
        "deleted": True,
        "records_removed": removed,
        "message": f"Done. All behavioral history has been deleted ({removed} records removed)."
    }
