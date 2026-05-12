import uuid
from datetime import datetime

# Restaurant stubs — venues known from user history + additional options per neighborhood
RESTAURANTS = [
    # River North
    {"venue_id": "VN_001", "venue_name": "Piccolo Sogno", "address": "464 N Milwaukee Ave, Chicago, IL", "cuisine": "Italian", "estimated_cost_per_person": 55, "rating": 4.7, "available_times": ["18:00", "18:30", "19:00", "19:30", "20:00"], "location_bucket": "River North"},
    {"venue_id": "VN_002", "venue_name": "RPM Italian", "address": "52 W Illinois St, Chicago, IL", "cuisine": "Italian", "estimated_cost_per_person": 65, "rating": 4.6, "available_times": ["17:30", "18:00", "19:00", "20:00", "20:30"], "location_bucket": "River North"},
    {"venue_id": "VN_003", "venue_name": "Bavette's Bar & Boeuf", "address": "218 W Kinzie St, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 70, "rating": 4.8, "available_times": ["18:00", "19:00", "20:00", "21:00"], "location_bucket": "River North"},
    {"venue_id": "VN_004", "venue_name": "GT Fish & Oyster", "address": "531 N Wells St, Chicago, IL", "cuisine": "Seafood", "estimated_cost_per_person": 60, "rating": 4.5, "available_times": ["17:00", "18:00", "19:00", "19:30", "20:00"], "location_bucket": "River North"},
    {"venue_id": "VN_005", "venue_name": "The Purple Pig", "address": "500 N Michigan Ave, Chicago, IL", "cuisine": "Mediterranean", "estimated_cost_per_person": 45, "rating": 4.6, "available_times": ["17:00", "18:00", "19:00", "22:00", "22:30"], "location_bucket": "River North"},
    {"venue_id": "VN_006", "venue_name": "Nico Osteria", "address": "1015 N Rush St, Chicago, IL", "cuisine": "Italian", "estimated_cost_per_person": 75, "rating": 4.4, "available_times": ["18:00", "19:00", "20:00"], "location_bucket": "River North"},
    {"venue_id": "VN_007", "venue_name": "Sunda New Asian", "address": "110 W Illinois St, Chicago, IL", "cuisine": "Asian", "estimated_cost_per_person": 50, "rating": 4.3, "available_times": ["17:30", "18:30", "19:30"], "location_bucket": "River North"},
    # Riverfront
    {"venue_id": "VN_008", "venue_name": "Chicago Riverwalk Café", "address": "180 N Michigan Ave, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 30, "rating": 4.2, "available_times": ["11:00", "12:00", "13:00", "14:00", "15:00"], "location_bucket": "Riverfront"},
    {"venue_id": "VN_009", "venue_name": "BOKA", "address": "1729 N Halsted St, Chicago, IL", "cuisine": "New American", "estimated_cost_per_person": 80, "rating": 4.7, "available_times": ["12:00", "12:30", "13:00", "13:30"], "location_bucket": "Riverfront"},
    {"venue_id": "VN_010", "venue_name": "Beatrix", "address": "519 N Clark St, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 35, "rating": 4.3, "available_times": ["11:00", "11:30", "12:00", "13:00", "14:00"], "location_bucket": "Riverfront"},
    {"venue_id": "VN_011", "venue_name": "City Winery Chicago", "address": "11 W Kinzie St, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 50, "rating": 4.2, "available_times": ["12:00", "13:00", "18:00", "19:00"], "location_bucket": "Riverfront"},
    # Lincoln Park
    {"venue_id": "VN_012", "venue_name": "Batter & Berries", "address": "2748 N Lincoln Ave, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 20, "rating": 4.6, "available_times": ["08:00", "09:00", "10:00", "11:00"], "location_bucket": "Lincoln Park"},
    {"venue_id": "VN_013", "venue_name": "North Pond", "address": "2610 N Cannon Dr, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 90, "rating": 4.5, "available_times": ["11:30", "12:00", "18:00", "19:00", "20:00"], "location_bucket": "Lincoln Park"},
    {"venue_id": "VN_014", "venue_name": "Café Ba-Ba-Reeba!", "address": "2024 N Halsted St, Chicago, IL", "cuisine": "Mediterranean", "estimated_cost_per_person": 40, "rating": 4.3, "available_times": ["12:00", "17:30", "18:00", "18:30"], "location_bucket": "Lincoln Park"},
    # Wicker Park
    {"venue_id": "VN_015", "venue_name": "Jam", "address": "3057 W Logan Blvd, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 18, "rating": 4.5, "available_times": ["08:00", "09:00", "10:00", "10:30", "11:00"], "location_bucket": "Wicker Park"},
    {"venue_id": "VN_016", "venue_name": "Dove's Luncheonette", "address": "1545 N Damen Ave, Chicago, IL", "cuisine": "Mexican", "estimated_cost_per_person": 22, "rating": 4.6, "available_times": ["09:00", "10:00", "11:00"], "location_bucket": "Wicker Park"},
    {"venue_id": "VN_017", "venue_name": "Big Star", "address": "1531 N Damen Ave, Chicago, IL", "cuisine": "Mexican", "estimated_cost_per_person": 20, "rating": 4.4, "available_times": ["11:00", "12:00", "17:00", "18:00", "22:00"], "location_bucket": "Wicker Park"},
    # Loop
    {"venue_id": "VN_018", "venue_name": "The Gage", "address": "24 S Michigan Ave, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 45, "rating": 4.4, "available_times": ["11:30", "12:00", "12:30", "13:00", "13:30"], "location_bucket": "Loop"},
    {"venue_id": "VN_019", "venue_name": "Cindy's", "address": "12 S Michigan Ave, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 55, "rating": 4.5, "available_times": ["11:30", "12:00", "13:00", "17:30", "18:00"], "location_bucket": "Loop"},
    {"venue_id": "VN_020", "venue_name": "Cochon Volant", "address": "100 W Monroe St, Chicago, IL", "cuisine": "French", "estimated_cost_per_person": 45, "rating": 4.3, "available_times": ["11:30", "12:00", "12:30", "13:00"], "location_bucket": "Loop"},
    # West Loop
    {"venue_id": "VN_021", "venue_name": "Au Cheval", "address": "800 W Randolph St, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 30, "rating": 4.7, "available_times": ["22:00", "22:30", "23:00"], "location_bucket": "West Loop"},
    {"venue_id": "VN_022", "venue_name": "Girl & the Goat", "address": "809 W Randolph St, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 65, "rating": 4.6, "available_times": ["17:30", "18:00", "18:30", "19:00", "20:00"], "location_bucket": "West Loop"},
    {"venue_id": "VN_023", "venue_name": "Randolph Street Market", "address": "1340 W Washington Blvd, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 35, "rating": 4.2, "available_times": ["12:00", "13:00", "18:00", "19:00"], "location_bucket": "West Loop"},
    {"venue_id": "VN_024", "venue_name": "Little Goat Diner", "address": "820 W Randolph St, Chicago, IL", "cuisine": "American", "estimated_cost_per_person": 25, "rating": 4.4, "available_times": ["08:00", "09:00", "10:00", "11:00", "12:00"], "location_bucket": "West Loop"},
]


def search_restaurants(location: str, date: str, time: str, party_size: int, cuisine: str | None) -> list[dict]:
    results = []
    for r in RESTAURANTS:
        if r["location_bucket"].lower() != location.lower():
            continue
        if cuisine and r["cuisine"].lower() != cuisine.lower():
            continue
        results.append(r)
    # Sort by rating descending as default (agent will re-rank by history)
    results.sort(key=lambda x: -x["rating"])
    return results


def book_restaurant(
    venue_id: str,
    venue_name: str,
    date: str,
    time: str,
    party_size: int,
    counterparty_name: str,
    counterparty_phone: str,
) -> dict:
    confirmation_id = "CONF-" + str(uuid.uuid4())[:8].upper()
    return {
        "booking_confirmed": True,
        "confirmation_id": confirmation_id,
        "venue_name": venue_name,
        "date": date,
        "time": time,
        "party_size": party_size,
        "error_message": None,
    }


def get_venue_by_id(venue_id: str) -> dict | None:
    for r in RESTAURANTS:
        if r["venue_id"] == venue_id:
            return r
    return None
