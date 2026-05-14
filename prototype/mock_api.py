import uuid

RESTAURANTS = [
    # River North
    {
        "venue_id": "RN001", "venue_name": "Piccolo Sogno",
        "address": "464 N Halsted St", "cuisine": "Italian",
        "estimated_cost_per_person": 65, "rating": 4.7, "location_bucket": "River North",
        "available_times": {
            "evening": ["17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"]
        }
    },
    {
        "venue_id": "RN002", "venue_name": "RPM Italian",
        "address": "52 W Illinois St", "cuisine": "Italian",
        "estimated_cost_per_person": 75, "rating": 4.6, "location_bucket": "River North",
        "available_times": {
            "evening": ["17:30", "18:00", "18:30", "19:00", "19:30", "20:00"]
        }
    },
    {
        "venue_id": "RN003", "venue_name": "Bavette's Bar & Boeuf",
        "address": "218 W Kinzie St", "cuisine": "American",
        "estimated_cost_per_person": 80, "rating": 4.7, "location_bucket": "River North",
        "available_times": {
            "evening": ["17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30"]
        }
    },
    {
        "venue_id": "RN004", "venue_name": "GT Fish & Oyster",
        "address": "531 N Wells St", "cuisine": "Seafood",
        "estimated_cost_per_person": 55, "rating": 4.5, "location_bucket": "River North",
        "available_times": {
            "evening": ["17:30", "18:00", "18:30", "19:00", "19:30", "20:00"]
        }
    },
    {
        "venue_id": "RN005", "venue_name": "The Purple Pig",
        "address": "500 N Michigan Ave", "cuisine": "Mediterranean",
        "estimated_cost_per_person": 45, "rating": 4.4, "location_bucket": "River North",
        "available_times": {
            "evening": ["17:30", "18:00", "19:00", "20:00", "21:00"],
            "late_night": ["21:30", "22:00", "22:30"]
        }
    },
    {
        "venue_id": "RN006", "venue_name": "Frontera Grill",
        "address": "445 N Clark St", "cuisine": "Mexican",
        "estimated_cost_per_person": 55, "rating": 4.6, "location_bucket": "River North",
        "available_times": {
            "afternoon": ["12:00", "12:30", "13:00"],
            "evening": ["17:30", "18:00", "19:00", "20:00"]
        }
    },
    # Riverfront
    {
        "venue_id": "RF001", "venue_name": "Chicago Riverwalk Café",
        "address": "1 Riverwalk Dr", "cuisine": "American",
        "estimated_cost_per_person": 30, "rating": 4.2, "location_bucket": "Riverfront",
        "available_times": {
            "morning": ["09:00", "09:30", "10:00", "10:30", "11:00"],
            "afternoon": ["12:00", "12:30", "13:00", "13:30", "14:00"]
        }
    },
    {
        "venue_id": "RF002", "venue_name": "BOKA",
        "address": "1729 N Halsted St", "cuisine": "New American",
        "estimated_cost_per_person": 85, "rating": 4.7, "location_bucket": "Riverfront",
        "available_times": {
            "afternoon": ["12:00", "12:30", "13:00", "13:30"],
            "evening": ["17:30", "18:00", "19:00"]
        }
    },
    {
        "venue_id": "RF003", "venue_name": "Beatrix",
        "address": "519 N Clark St", "cuisine": "American",
        "estimated_cost_per_person": 35, "rating": 4.3, "location_bucket": "Riverfront",
        "available_times": {
            "morning": ["08:00", "08:30", "09:00", "09:30"],
            "afternoon": ["12:00", "12:30", "13:00", "14:00"]
        }
    },
    {
        "venue_id": "RF004", "venue_name": "South Water Kitchen",
        "address": "225 N Wabash Ave", "cuisine": "American",
        "estimated_cost_per_person": 45, "rating": 4.3, "location_bucket": "Riverfront",
        "available_times": {
            "afternoon": ["12:00", "12:30", "13:00"],
            "evening": ["17:30", "18:00", "19:00"]
        }
    },
    # Lincoln Park
    {
        "venue_id": "LP001", "venue_name": "Batter & Berries",
        "address": "2748 N Lincoln Ave", "cuisine": "American",
        "estimated_cost_per_person": 20, "rating": 4.5, "location_bucket": "Lincoln Park",
        "available_times": {
            "morning": ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00"]
        }
    },
    {
        "venue_id": "LP002", "venue_name": "Gemini Bistro",
        "address": "2075 N Lincoln Ave", "cuisine": "American",
        "estimated_cost_per_person": 40, "rating": 4.4, "location_bucket": "Lincoln Park",
        "available_times": {
            "afternoon": ["12:00", "12:30", "13:00"],
            "evening": ["17:30", "18:00", "19:00", "20:00"]
        }
    },
    # Wicker Park
    {
        "venue_id": "WP001", "venue_name": "Jam",
        "address": "3057 W Logan Blvd", "cuisine": "American",
        "estimated_cost_per_person": 20, "rating": 4.5, "location_bucket": "Wicker Park",
        "available_times": {
            "morning": ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30"]
        }
    },
    {
        "venue_id": "WP002", "venue_name": "Dove's Luncheonette",
        "address": "1545 N Damen Ave", "cuisine": "Mexican",
        "estimated_cost_per_person": 20, "rating": 4.6, "location_bucket": "Wicker Park",
        "available_times": {
            "morning": ["09:00", "09:30", "10:00", "10:30", "11:00"]
        }
    },
    {
        "venue_id": "WP003", "venue_name": "Big Star",
        "address": "1531 N Damen Ave", "cuisine": "Mexican",
        "estimated_cost_per_person": 20, "rating": 4.4, "location_bucket": "Wicker Park",
        "available_times": {
            "afternoon": ["12:00", "12:30", "13:00"],
            "late_night": ["21:30", "22:00", "22:30", "23:00"]
        }
    },
    # Loop
    {
        "venue_id": "LO001", "venue_name": "The Gage",
        "address": "24 S Michigan Ave", "cuisine": "American",
        "estimated_cost_per_person": 40, "rating": 4.3, "location_bucket": "Loop",
        "available_times": {
            "afternoon": ["12:00", "12:30", "13:00", "13:30", "14:00"],
            "evening": ["17:30", "18:00", "19:00"]
        }
    },
    {
        "venue_id": "LO002", "venue_name": "Cindy's",
        "address": "12 S Michigan Ave", "cuisine": "American",
        "estimated_cost_per_person": 55, "rating": 4.5, "location_bucket": "Loop",
        "available_times": {
            "afternoon": ["12:00", "12:30", "13:00", "14:00"],
            "evening": ["17:30", "18:00", "19:00", "20:00"]
        }
    },
    {
        "venue_id": "LO003", "venue_name": "Millennium Park Grille",
        "address": "11 N Michigan Ave", "cuisine": "American",
        "estimated_cost_per_person": 45, "rating": 4.2, "location_bucket": "Loop",
        "available_times": {
            "afternoon": ["12:00", "12:30", "13:00"]
        }
    },
    # West Loop
    {
        "venue_id": "WL001", "venue_name": "Au Cheval",
        "address": "800 W Randolph St", "cuisine": "American",
        "estimated_cost_per_person": 35, "rating": 4.5, "location_bucket": "West Loop",
        "available_times": {
            "evening": ["18:00", "18:30", "19:00", "20:00", "21:00"],
            "late_night": ["21:30", "22:00", "22:30", "23:00"]
        }
    },
    {
        "venue_id": "WL002", "venue_name": "Girl & the Goat",
        "address": "809 W Randolph St", "cuisine": "American",
        "estimated_cost_per_person": 60, "rating": 4.6, "location_bucket": "West Loop",
        "available_times": {
            "evening": ["17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"]
        }
    },
    {
        "venue_id": "WL003", "venue_name": "Avec",
        "address": "615 W Randolph St", "cuisine": "Mediterranean",
        "estimated_cost_per_person": 50, "rating": 4.6, "location_bucket": "West Loop",
        "available_times": {
            "evening": ["17:30", "18:00", "19:00", "20:00"],
            "late_night": ["21:30", "22:00"]
        }
    },
    {
        "venue_id": "WL004", "venue_name": "Monteverde",
        "address": "1020 W Madison St", "cuisine": "Italian",
        "estimated_cost_per_person": 65, "rating": 4.7, "location_bucket": "West Loop",
        "available_times": {
            "evening": ["17:30", "18:00", "18:30", "19:00", "19:30", "20:00"]
        }
    },
]

_venue_index = {r["venue_id"]: r for r in RESTAURANTS}


def search_restaurants(location: str, time_bucket: str, cuisine: str = None) -> list:
    results = []
    for r in RESTAURANTS:
        known_buckets = {r2["location_bucket"].lower() for r2 in RESTAURANTS}
        if location.lower() in known_buckets and r["location_bucket"].lower() != location.lower():
            continue
        if cuisine and r["cuisine"].lower() != cuisine.lower():
            continue
        times = r["available_times"].get(time_bucket, [])
        if not times:
            continue
        results.append({
            "venue_id": r["venue_id"],
            "venue_name": r["venue_name"],
            "address": r["address"],
            "cuisine": r["cuisine"],
            "estimated_cost_per_person": r["estimated_cost_per_person"],
            "rating": r["rating"],
            "location_bucket": r["location_bucket"],
            "available_times": times,
        })
    return results


def make_booking(venue_id: str, date: str, time: str, party_size: int, name: str, phone: str) -> dict:
    restaurant = _venue_index.get(venue_id)
    if not restaurant:
        return {
            "booking_confirmed": False,
            "confirmation_id": None,
            "venue_name": None,
            "date": date,
            "time": time,
            "party_size": party_size,
            "error_message": "Restaurant not found. Please try searching again."
        }
    confirmation_id = f"OT-{uuid.uuid4().hex[:8].upper()}"
    return {
        "booking_confirmed": True,
        "confirmation_id": confirmation_id,
        "venue_name": restaurant["venue_name"],
        "address": restaurant["address"],
        "date": date,
        "time": time,
        "party_size": party_size,
        "error_message": None
    }
