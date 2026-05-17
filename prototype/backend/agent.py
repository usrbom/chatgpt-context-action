"""Demo agent — scripted booking flow, Claude CLI for general chat.

Booking flow (state machine, no API key):
INITIAL → CLARIFYING → SELECTING → CONFIRMING → COLLECTING_NAME → COLLECTING_PHONE → DONE

General chat: routed to `claude --print` using the existing Claude Code subscription.
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timedelta

import db
import tools

db.init_db()

# ── Session state ──────────────────────────────────────────────────────────────

def _new_state() -> dict:
    return {
        "state": "INITIAL",
        "params": {
            "location": None,
            "date": None,
            "time_bucket": None,
            "party_size": 1,
            "cuisine": None,
        },
        "asking_for": None,
        "recommendations": [],
        "history_context_applies": False,
        "selected_venue": None,
        "selected_time": None,
        "name": None,
    }

_sessions: dict[str, dict] = {}


def _load_state(session_id: str) -> dict:
    if session_id in _sessions:
        return _sessions[session_id]
    raw = db.load_session(session_id)
    if raw:
        state = json.loads(raw)
        _sessions[session_id] = state
        return state
    state = _new_state()
    _sessions[session_id] = state
    return state


def _persist_state(session_id: str) -> None:
    if session_id in _sessions:
        db.save_session(session_id, json.dumps(_sessions[session_id]))


# ── Intent parsing ─────────────────────────────────────────────────────────────

NEIGHBORHOODS: dict[str, str] = {
    # Chicago
    "river north": "River North",
    "riverfront": "Riverfront",
    "lincoln park": "Lincoln Park",
    "wicker park": "Wicker Park",
    "the loop": "Loop",
    "west loop": "West Loop",
    "loop": "Loop",
    # Los Angeles
    "westwood": "Westwood",
    "santa monica": "Santa Monica",
    "beverly hills": "Beverly Hills",
    "west hollywood": "West Hollywood",
    "weho": "West Hollywood",
    "silver lake": "Silver Lake",
    "silverlake": "Silver Lake",
    "downtown la": "Downtown LA",
    "downtown los angeles": "Downtown LA",
    "dtla": "Downtown LA",
    "venice beach": "Venice Beach",
    "venice": "Venice Beach",
    "marina del rey": "Marina del Rey",
    "los feliz": "Los Feliz",
    "culver city": "Culver City",
    "brentwood": "Brentwood",
    "pasadena": "Pasadena",
    # New York
    "midtown": "Midtown",
    "west village": "West Village",
    "soho": "SoHo",
    "brooklyn": "Brooklyn",
    "lower east side": "Lower East Side",
    "les": "Lower East Side",
    "upper west side": "Upper West Side",
    "chelsea": "Chelsea",
    "tribeca": "Tribeca",
    # San Francisco
    "mission": "Mission",
    "north beach": "North Beach",
    "hayes valley": "Hayes Valley",
    "financial district": "Financial District",
    "soma": "SoMa",
    "castro": "Castro",
    # Miami
    "south beach": "South Beach",
    "wynwood": "Wynwood",
    "brickell": "Brickell",
    # Other cities
    "georgetown": "Georgetown",
    "back bay": "Back Bay",
    "capitol hill": "Capitol Hill",
    "east austin": "East Austin",
}

CUISINES = ["Italian", "American", "Mediterranean", "Seafood", "New American", "Mexican", "Asian", "French",
            "Japanese", "Thai", "Ethiopian", "Indian", "Chinese", "Korean", "Spanish", "Greek"]

_TIME_KEYWORDS: list[tuple[str, list[str]]] = [
    ("late_night", ["late night", "late-night", "after 10", "after 11", "after midnight"]),
    ("morning",    ["morning", "breakfast", "brunch"]),
    ("afternoon",  ["lunch", "afternoon", "midday", "noon"]),
    ("evening",    ["dinner", "evening", "tonight", "supper", "night"]),
]

_DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def _parse_location(text: str) -> str | None:
    low = text.lower()
    for key, val in NEIGHBORHOODS.items():
        if key in low:
            return val
    return None


def _parse_time_bucket(text: str) -> str:
    low = text.lower()
    for bucket, keywords in _TIME_KEYWORDS:
        for kw in keywords:
            if kw in low:
                return bucket
    return "evening"


def _parse_party_size(text: str) -> int:
    low = text.lower()
    m = re.search(r'for\s+(\d+)|(\d+)\s*(?:people|guests?|person|of us)', low)
    if m:
        return int(m.group(1) or m.group(2))
    for word, num in _NUMBER_WORDS.items():
        if re.search(rf'\bfor {word}\b|\b{word} (?:people|guests?|person)\b', low):
            return num
    return 1


def _parse_party_size_explicit(text: str) -> int | None:
    """Only returns a value when party size is clearly stated — avoids treating '1' as party of 1."""
    low = text.lower()
    m = re.search(r'(?:party of|for|table for|group of)\s+(\d+)', low)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)\s+(?:people|guests?|person|of us)', low)
    if m:
        return int(m.group(1))
    m = re.search(r'(?:party size|size)\s+(?:to|of)\s+(\d+)', low)
    if m:
        return int(m.group(1))
    m = re.search(r'change\s+(?:the\s+)?(?:party\s+)?(?:size\s+)?to\s+(\d+)', low)
    if m:
        return int(m.group(1))
    for word, num in _NUMBER_WORDS.items():
        if re.search(rf'\bfor {word}\b|\b{word} (?:people|guests?|person)\b', low):
            return num
    return None


def _parse_time_bucket_explicit(text: str) -> str | None:
    """Only returns a value when a time keyword is explicitly present."""
    low = text.lower()
    for bucket, keywords in _TIME_KEYWORDS:
        for kw in keywords:
            if kw in low:
                return bucket
    return None


def _parse_cuisine(text: str) -> str | None:
    low = text.lower()
    for c in CUISINES:
        if c.lower() in low:
            return c
    return None


_MEETING_KEYWORDS = ["meeting", "meet up", "catching up", "catch up", "going out",
                     "hanging out", "hang out", "get together", "getting together",
                     "date tonight", "date today", "out with", "dinner with", "lunch with",
                     "drinks with", "going to see", "seeing friends", "seeing my"]

_GENERAL_CHAT_SYSTEM = (
    "You are a helpful assistant built into a restaurant booking app called ChatGPT. "
    "Chat naturally with the user. Keep responses brief — 1 to 3 sentences. "
    "If what they say sounds like they want to find or book a restaurant, offer to help. "
    "Otherwise just respond like a friendly assistant would. No markdown, no bullet points."
)


def _handle_general_chat(msg: str) -> str:
    """Route general (non-booking) messages through Claude CLI using the existing subscription."""
    low = msg.lower().strip()

    # Proactively offer restaurant help for clear social/meeting context
    if any(kw in low for kw in _MEETING_KEYWORDS):
        time_hint = ""
        if any(w in low for w in ["tonight", "this evening", "later today"]):
            time_hint = " tonight"
        elif any(w in low for w in ["tomorrow", "this weekend", "this friday", "this saturday"]):
            time_hint = " then"
        elif any(w in low for w in ["lunch", "afternoon", "midday"]):
            time_hint = " for lunch"
        return f"Would you like me to find a restaurant{time_hint}? Just tell me the neighborhood and I'll pull up options."

    # Call Claude CLI for everything else
    prompt = f"{_GENERAL_CHAT_SYSTEM}\n\nUser: {msg}"
    try:
        result = subprocess.run(
            ["claude", "--print", prompt],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    # Fallback if CLI unavailable
    return "I can help you find and book a restaurant. Just tell me where and when."


_RESERVATION_KEYWORDS = [
    "book", "reserve", "reservation", "table",
    "restaurant", "eat", "eating", "food", "dining", "dine",
    "dinner", "lunch", "brunch", "breakfast", "supper",
    "find me", "suggest", "recommend", "looking for a place",
    "where should i", "where to eat", "place to eat",
    "hungry", "meal", "cuisine",
    "availab", "available", "check availability", "find availability",
    "opening", "open table", "spot", "seats",
]

def _has_reservation_intent(text: str) -> bool:
    low = text.lower()
    if any(kw in low for kw in _RESERVATION_KEYWORDS):
        return True
    # A location name alone is enough intent (e.g. "Westwood tonight")
    if _parse_location(text):
        return True
    return False


def _parse_date(text: str) -> str | None:
    low = text.lower()
    today = datetime.now()

    if "today" in low or "tonight" in low:
        return today.strftime("%Y-%m-%d")
    if "tomorrow" in low:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    is_next = "next" in low
    for i, day in enumerate(_DAY_NAMES):
        if day in low:
            today_dow = today.weekday()
            delta = (i - today_dow) % 7
            if delta == 0 and "this" in low:
                delta = 7  # "this <day>" when today IS that day → next occurrence
            elif delta == 0:
                delta = 7  # bare day name = next occurrence
            if is_next and delta <= 7:
                delta += 7
            return (today + timedelta(days=delta)).strftime("%Y-%m-%d")

    # "May 15", "June 3"
    m = re.search(
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})', low
    )
    if m:
        month_map = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                     "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
        try:
            return datetime(today.year, month_map[m.group(1)[:3]], int(m.group(2))).strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def _parse_intent(text: str) -> dict:
    return {
        "location": _parse_location(text),
        "date": _parse_date(text),
        "time_bucket": _parse_time_bucket(text),
        "party_size": _parse_party_size(text),
        "cuisine": _parse_cuisine(text),
    }


def _is_question(text: str) -> bool:
    low = text.lower()
    if "?" in text:
        return True
    return any(low.startswith(w) for w in [
        "why", "what", "how", "when", "where", "who",
        "can you", "could you", "explain", "tell me",
        "i thought", "i expected", "i was",
    ])


def _answer_question(msg: str, state: dict) -> str:
    low = msg.lower()
    params = state["params"]
    tb = params.get("time_bucket", "evening")
    tb_label = {"morning": "morning", "afternoon": "afternoon/lunch",
                "evening": "evening/dinner", "late_night": "late night"}.get(tb, tb)

    # Why a specific time / meal period?
    time_words = ["evening", "dinner", "night", "morning", "lunch", "afternoon",
                  "late", "time", "meal", "brunch", "breakfast"]
    if ("why" in low or "how did you" in low or "i thought" in low) and any(w in low for w in time_words):
        if tb and tb != "evening":
            intro = f"I inferred {tb_label} from your message."
        else:
            intro = "I defaulted to evening since no specific time was mentioned."
        return f"{intro} Just say the time you'd like — \"lunch\", \"afternoon\", or \"late night\" — and I'll search accordingly."

    # Why this location?
    loc = params.get("location", "")
    if "why" in low and loc and loc.lower() in low:
        return f"You mentioned {loc} in your request. To search somewhere else, just name a different neighborhood."

    # Why these restaurants / how is ranking done?
    if any(w in low for w in ["why these", "how did you pick", "how are these ranked",
                               "why this order", "why this list", "how does it work",
                               "explain how", "explain the ranking", "how is this ranked",
                               "how is the ranking", "ranking work", "why are these",
                               "ranked this way", "these ranked"]):
        if state.get("history_context_applies"):
            return (
                "These are ranked based on your past visits — places you've booked more often "
                "and more recently appear higher in the list."
            )
        return "These are ranked by rating since I don't have past visits on record for this neighborhood and time."

    # What time / when?
    if any(w in low for w in ["what time", "which time", "when is this"]):
        times = {"morning": "around 9:00am", "afternoon": "around 1:00pm",
                 "evening": "around 7:00pm", "late_night": "around 10:00pm"}
        return (
            f"I'm searching for {times.get(tb, '7:00pm')}. "
            f"You can ask for a specific time and I'll update the search."
        )

    # Party size?
    if any(w in low for w in ["how many", "party size", "how large", "number of people"]):
        return f"Currently searching for a party of {params.get('party_size', 2)}. Say \"party of X\" to change it."

    # What neighborhood / location?
    if any(w in low for w in ["what neighborhood", "which area", "where is this", "what area"]):
        return f"Searching in {loc}. Just name a different neighborhood to search there instead."

    # Generic fallback — still helpful, not a dead end
    n = len(state.get("recommendations", []))
    return (
        f"To change your search, just say what you'd like — a different neighborhood, "
        f"party size, cuisine, or time. Or choose from the {n} options above by number."
    )


_COVERED_NEIGHBORHOODS = [
    "River North, West Loop, Lincoln Park (Chicago)",
    "Santa Monica, Westwood, Beverly Hills, Venice Beach (LA)",
    "West Village, SoHo, Midtown, Brooklyn (NYC)",
    "Mission, North Beach, Hayes Valley (SF)",
    "South Beach, Wynwood, Brickell (Miami)",
]


def _is_known_location(name: str) -> bool:
    """True if name fuzzy-matches a location bucket in the mock API."""
    from mock_api import _LOCATION_INDEX
    loc_lower = name.lower()
    return bool(_parse_location(name)) or any(
        loc_lower in k or k in loc_lower for k in _LOCATION_INDEX.keys()
    )


def _extract_location_attempt(text: str) -> str | None:
    """Return a candidate place name from 'in/at/near X' patterns if X is not a known neighborhood."""
    m = re.search(
        r'\b(?:in|at|near|around)\s+([A-Za-z][a-zA-Z ]{1,25}?)(?=\s+(?:for|on|this|next|tonight|today|tomorrow|a\s|\d)|[,.]|$)',
        text.strip(),
    )
    if m:
        candidate = m.group(1).strip().title()
        if candidate and not _parse_location(candidate):
            return candidate
    return None


def _unknown_location_response(location_name: str) -> dict:
    return {
        "response": (
            f"I don't have restaurants listed in {location_name}. "
            f"Here are neighborhoods I can search:\n\n"
            + "\n".join(f"• {c}" for c in _COVERED_NEIGHBORHOODS)
            + "\n\nWhich one works for you?"
        ),
        "tool_log": [],
    }


def _looks_like_location_attempt(text: str, current_recs: list) -> bool:
    """True when the user seems to be naming a place, even if it's not in NEIGHBORHOODS."""
    stripped = text.strip()
    if len(stripped.split()) > 5:
        return False
    if "?" in stripped or "!" in stripped:
        return False
    if re.match(r'^\d+$', stripped):
        return False
    low = stripped.lower()
    for r in current_recs:
        if r["venue_name"].lower() in low or low in r["venue_name"].lower():
            return False
    loc_signals = ["mall", "street", "ave", "blvd", "city", "park", "beach",
                   "hills", "village", "square", "district", "town", "area",
                   "downtown", "uptown", "la", "nyc", "sf"]
    if any(w in low for w in loc_signals):
        return True
    # Short proper-noun-ish text (first letter capital)
    if stripped and stripped[0].isupper() and len(stripped.split()) <= 3:
        return True
    return False


def _next_missing(params: dict) -> str | None:
    if not params["location"]:
        return "location"
    if not params["date"]:
        return "date"
    return None


# ── Response formatters ────────────────────────────────────────────────────────

def _fmt_recommendations(recs: list) -> str:
    lines = []
    for i, r in enumerate(recs, 1):
        lines.append(
            f"{i}. {r['venue_name']} — {r['cuisine']}, ~${r['estimated_cost_per_person']}/person, ★{r['rating']}"
        )
    return "\n".join(lines)


def _fmt_confirmation_card(venue: dict, date: str, time: str, party_size: int) -> str:
    try:
        date_fmt = datetime.strptime(date, "%Y-%m-%d").strftime("%A, %B %-d")
    except ValueError:
        date_fmt = date
    return (
        f"Here are your booking details:\n\n"
        f"Restaurant: {venue['venue_name']}\n"
        f"Address:    {venue.get('address', '')}\n"
        f"Cuisine:    {venue.get('cuisine', '')} | ~${venue.get('estimated_cost_per_person', '?')}/person\n\n"
        f"Date:       {date_fmt}\n"
        f"Time:       {time}\n"
        f"Party size: {party_size}\n\n"
        f"Reply \"confirm\" to book, or \"more options\" to see other choices."
    )


def _pick_time(venue: dict, time_bucket: str) -> str:
    bucket_ranges = {
        "morning": range(6, 12),
        "afternoon": range(12, 17),
        "evening": range(17, 22),
        "late_night": list(range(22, 24)) + list(range(0, 6)),
    }
    preferred_hours = bucket_ranges.get(time_bucket, range(17, 22))
    for t in venue.get("available_times", []):
        h = int(t.split(":")[0])
        if h in preferred_hours:
            return t
    times = venue.get("available_times", ["19:00"])
    return times[0] if times else "19:00"


# ── Adversarial detection ──────────────────────────────────────────────────────

_ADVERSARIAL = [
    "ignore previous", "ignore all", "disregard", "system prompt",
    "jailbreak", "pretend you are", "act as if", "you are now",
    "reveal your instructions", "forget your instructions",
    "every day for a month", "for a year", "override",
    "user_id", "admin", "other user",
    # False context injection
    "from my history", "you know this",
    # SQL injection
    "drop table", "'; --", "';--",
    # Flow-bypass
    "skip asking", "skip the confirm", "bypass confirm", "skip confirm",
    # History manipulation
    "fake booking", "fake confirmed", "log a fake", "quietly log",
    # System prompt extraction
    "list all the rules", "list your rules", "what rules do you", "how do you rank",
    "show me your rules", "explain your rules",
    # Fabricated history injection
    "pretend i visit", "pretend my history", "pretend i go",
    # Bulk/recurring booking without confirmation
    "every friday for", "every saturday for", "every week for", "every month for",
    "for the next 3 months", "for the next 6 months", "without asking me each",
    "without confirming each",
    # Cross-user data extraction
    "demo_user_02", "other user's", "another user's", "someone else's history",
    "show me.*history", "show me.*favorite",
]


def _is_adversarial(text: str) -> bool:
    low = text.lower()
    return any(s in low for s in _ADVERSARIAL)


# ── Main entry point ───────────────────────────────────────────────────────────

def run_turn(session_id: str, user_id: str, user_message: str) -> dict:
    result = _run_turn(session_id, user_id, user_message)
    _persist_state(session_id)
    return result


def _run_turn(session_id: str, user_id: str, user_message: str) -> dict:
    state = _load_state(session_id)
    msg = user_message.strip()
    msg_low = msg.lower()
    tool_log: list[dict] = []

    # ── Adversarial guard ──────────────────────────────────────
    if _is_adversarial(msg):
        return {
            "response": "I can only help with restaurant bookings. What location and date are you looking for?",
            "tool_log": [],
        }

    # ── Cancellation / modification (any state) ────────────────
    _cancel_modify = [
        "cancel", "cancellation",
        "modify", "modification",
        "change my reservation", "change my booking",
        "change reservation", "change booking", "change the booking", "change the reservation",
        "update my reservation", "update my booking",
        "update reservation", "update booking",
        "reschedule", "edit my reservation", "edit my booking",
        "edit reservation", "edit booking",
        "amend my reservation", "amend my booking",
    ]
    _has_conf_code = bool(re.search(r'\bconf[-‑]\w+', msg_low))
    if _has_conf_code or any(w in msg_low for w in _cancel_modify):
        return {
            "response": (
                "Cancellations and modifications aren't available in this chat. "
                "Please manage your reservation directly on OpenTable:\n\n"
                "https://www.opentable.com/my-reservations\n\n"
                "You'll need the confirmation number and the name used for the booking."
            ),
            "tool_log": [],
        }

    # ── Privacy commands (any state) ──────────────────────────
    if any(p in msg_low for p in ["what do you know", "show my history", "show patterns", "what patterns"]):
        result = tools.show_patterns(user_id)
        tool_log.append({"tool": "show_patterns", "input": {"user_id": user_id}, "output": result})
        history = result.get("restaurant_history", [])
        if not history:
            response = "I don't have any behavioral history for you yet."
        else:
            lines = [
                f"- {r['venue_name']} ({r['location_bucket']}, {r['cuisine']}) — {r['visit_count']} visit(s)"
                for r in history[:8]
            ]
            response = "Here's what I know from your past bookings:\n\n" + "\n".join(lines)
        return {"response": response, "tool_log": tool_log}

    if any(p in msg_low for p in ["forget everything", "delete my history", "stop learning from me"]):
        if state["state"] == "AWAITING_FORGET_CONFIRM":
            result = tools.forget_me(user_id)
            tool_log.append({"tool": "forget_me", "input": {"user_id": user_id}, "output": result})
            state.update(_new_state())
            return {"response": result["message"], "tool_log": tool_log}
        state["state"] = "AWAITING_FORGET_CONFIRM"
        return {
            "response": "This will permanently delete all your behavioral history. Reply \"confirm delete\" to proceed.",
            "tool_log": [],
        }

    # ── DONE (booking just completed) ─────────────────────────
    # No handler exists for DONE, so it falls through to INITIAL and confuses Claude.
    # Reset state so the next message is treated as a fresh start.
    if state["state"] == "DONE":
        state.update(_new_state())
        _post_booking_ack = {"yes", "yeah", "yep", "ok", "okay", "sure", "thanks",
                             "thank you", "great", "perfect", "awesome", "nice"}
        if msg_low.strip() in _post_booking_ack:
            return {"response": "Happy to help. Just say when you'd like to find another restaurant.", "tool_log": []}
        # Non-acknowledgment message — fall through and handle as a new request

    if msg_low == "confirm delete" and state["state"] == "AWAITING_FORGET_CONFIRM":
        result = tools.forget_me(user_id)
        tool_log.append({"tool": "forget_me", "input": {"user_id": user_id}, "output": result})
        state.update(_new_state())
        return {"response": result["message"], "tool_log": tool_log}

    # ── COLLECTING_PHONE ───────────────────────────────────────
    if state["state"] == "COLLECTING_PHONE":
        phone = re.sub(r"[^\d+\-\(\) ]", "", msg).strip()
        if len(re.sub(r"\D", "", phone)) < 7:
            return {"response": "Please enter a valid phone number.", "tool_log": []}
        state["name"] = state.get("name", "Guest")
        venue = state["selected_venue"]
        params = state["params"]
        tool_input = {
            "user_id": user_id,
            "venue_id": venue["venue_id"],
            "venue_name": venue["venue_name"],
            "date": params["date"],
            "time": state["selected_time"],
            "party_size": params["party_size"],
            "counterparty_name": state["name"],
            "counterparty_phone": phone,
        }
        result = tools.book_dining(**tool_input, session_id=session_id)
        tool_log.append({"tool": "book_dining", "input": tool_input, "output": result})
        state["state"] = "DONE"
        if result["booking_confirmed"]:
            try:
                date_fmt = datetime.strptime(params["date"], "%Y-%m-%d").strftime("%A, %B %-d")
            except ValueError:
                date_fmt = params["date"]
            response = (
                f"Reservation confirmed.\n\n"
                f"Confirmation: {result['confirmation_id']}\n"
                f"Restaurant:   {venue['venue_name']}\n"
                f"Date:         {date_fmt} at {state['selected_time']}\n"
                f"Party size:   {params['party_size']}\n"
                f"Name:         {state['name']}"
            )
        else:
            response = (
                "The booking didn't go through. "
                "You can try again or book directly at OpenTable: https://www.opentable.com"
            )
        return {"response": response, "tool_log": tool_log}

    # ── COLLECTING_NAME ────────────────────────────────────────
    if state["state"] == "COLLECTING_NAME":
        name = msg.strip()
        if len(name) < 2:
            return {"response": "Please enter the name for the reservation.", "tool_log": []}
        state["name"] = name
        state["state"] = "COLLECTING_PHONE"
        return {"response": "And your phone number?", "tool_log": []}

    # ── CONFIRMING ─────────────────────────────────────────────
    if state["state"] == "CONFIRMING":
        if any(w in msg_low for w in ["confirm", "yes", "book it", "book that", "looks good", "go ahead", "perfect", "sounds good", "that works"]):
            state["state"] = "COLLECTING_NAME"
            return {"response": "What name should the reservation be under?", "tool_log": []}

        venue = state["selected_venue"]

        # ── Detect amendments to booking params ────────────────
        new_party    = _parse_party_size_explicit(msg)
        new_date     = _parse_date(msg)
        new_tb       = _parse_time_bucket_explicit(msg)
        new_location = _parse_location(msg)
        new_cuisine  = _parse_cuisine(msg)

        amended = False
        needs_new_search = False
        if new_party is not None and new_party != state["params"]["party_size"]:
            state["params"]["party_size"] = new_party
            amended = True
        if new_date and new_date != state["params"]["date"]:
            state["params"]["date"] = new_date
            amended = True
        if new_tb and new_tb != state["params"]["time_bucket"]:
            state["params"]["time_bucket"] = new_tb
            state["selected_time"] = _pick_time(venue, new_tb)
            amended = True
        if new_location and new_location != state["params"]["location"]:
            state["params"]["location"] = new_location
            amended = True
            needs_new_search = True
        if new_cuisine and new_cuisine != state["params"]["cuisine"]:
            state["params"]["cuisine"] = new_cuisine
            amended = True
            needs_new_search = True

        if amended:
            if needs_new_search:
                return _do_recommendations(session_id, user_id, state, tool_log)
            state["selected_time"] = _pick_time(venue, state["params"]["time_bucket"])
            return {"response": _fmt_confirmation_card(venue, state["params"]["date"], state["selected_time"], state["params"]["party_size"]), "tool_log": []}

        # Asking about times / wanting a different time for the SAME restaurant
        _time_change = ["other time", "other times", "different time", "change time",
                        "check time", "available time", "what time", "which time",
                        "earlier", "later", "another time", "availab"]
        if any(w in msg_low for w in _time_change):
            times = venue.get("available_times", [])
            times_str = ", ".join(times) if times else "your requested time"
            return {
                "response": (
                    f"{venue['venue_name']} has these time slots available: {times_str}.\n\n"
                    "Reply with the time you'd like (e.g. \"17:00\" or \"5pm\")."
                ),
                "tool_log": [],
            }

        # Explicit time input — update and re-show confirmation card
        time_m = re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b|\b(\d{1,2})\s*(am|pm)\b', msg_low)
        if time_m:
            if time_m.group(1):
                hour, minute, meridiem = int(time_m.group(1)), int(time_m.group(2)), time_m.group(3)
            else:
                hour, minute, meridiem = int(time_m.group(4)), 0, time_m.group(5)
            if meridiem == "pm" and hour < 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
            new_time = f"{hour:02d}:{minute:02d}"
            available = venue.get("available_times", [])
            if available and new_time not in available:
                closest = min(available, key=lambda t: abs(int(t.split(":")[0]) * 60 + int(t.split(":")[1]) - hour * 60 - minute))
                return {
                    "response": (
                        f"{new_time} isn't available. The closest slot is {closest}.\n\n"
                        f"Reply \"{closest}\" to use that time, or choose from: {', '.join(available)}."
                    ),
                    "tool_log": [],
                }
            state["selected_time"] = new_time
            return {"response": _fmt_confirmation_card(venue, state["params"]["date"], new_time, state["params"]["party_size"]), "tool_log": []}

        # Wanting a different RESTAURANT — require explicit restaurant-change language
        if re.search(r'\bno\b|\bmore options\b|\bsomething else\b|\bdifferent restaurant\b|\bother restaurant\b|\bother place\b|\bdifferent place\b|\bcancel\b', msg_low):
            recs = state["recommendations"]
            if len(recs) <= 1:
                return {"response": "No other options available for that search. Try a different location or cuisine.", "tool_log": []}
            state["state"] = "SELECTING"
            return {
                "response": "Here are the other options:\n\n" + _fmt_recommendations(recs),
                "tool_log": [],
            }

        return {"response": "Reply \"confirm\" to book, or say a time like \"17:00\" or \"5pm\" to change it. Say \"more options\" to see other restaurants.", "tool_log": []}

    # ── SELECTING ──────────────────────────────────────────────
    if state["state"] == "SELECTING":
        recs = state["recommendations"]

        # Answer questions — but first check if the question embeds a param change
        if _is_question(msg):
            new_party    = _parse_party_size_explicit(msg)
            new_location = _parse_location(msg)
            new_date     = _parse_date(msg)
            new_tb       = _parse_time_bucket_explicit(msg)
            params_changed = False
            if new_party is not None and new_party != state["params"]["party_size"]:
                state["params"]["party_size"] = new_party
                params_changed = True
            if new_location and new_location != state["params"]["location"]:
                state["params"]["location"] = new_location
                params_changed = True
            if new_date and new_date != state["params"]["date"]:
                state["params"]["date"] = new_date
                params_changed = True
            if new_tb and new_tb != state["params"]["time_bucket"]:
                state["params"]["time_bucket"] = new_tb
                params_changed = True
            if params_changed:
                return _do_recommendations(session_id, user_id, state, tool_log)
            return {"response": _answer_question(msg, state), "tool_log": []}

        # ── Try to find a selection FIRST ──────────────────────
        # If the user selected a venue, apply any param updates from the same
        # message and go straight to CONFIRMING — don't re-run search.
        selected = None

        m = re.match(r'^(\d+)$', msg.strip())
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(recs):
                selected = recs[idx]

        if not selected:
            # Also try "number 2", "#3", "option 1", "the first one", etc.
            m2 = re.search(r'(?:number|option|#)\s*(\d+)|(?:^|\s)(first|second|third|fourth|fifth)(?:\s|$)', msg_low)
            if m2:
                ordinals = {"first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4}
                if m2.group(1):
                    idx = int(m2.group(1)) - 1
                else:
                    idx = ordinals.get(m2.group(2).strip(), -1)
                if 0 <= idx < len(recs):
                    selected = recs[idx]

        if not selected:
            for r in recs:
                if r["venue_name"].lower() in msg_low or msg_low in r["venue_name"].lower():
                    selected = r
                    break

        if selected:
            # Apply any param changes from this same message before confirming
            new_party = _parse_party_size_explicit(msg)
            new_date  = _parse_date(msg)
            new_tb    = _parse_time_bucket_explicit(msg)
            if new_party is not None:
                state["params"]["party_size"] = new_party
            if new_date:
                state["params"]["date"] = new_date
            if new_tb:
                state["params"]["time_bucket"] = new_tb
            state["selected_venue"] = selected
            state["selected_time"] = _pick_time(selected, state["params"]["time_bucket"])
            state["state"] = "CONFIRMING"
            card = _fmt_confirmation_card(selected, state["params"]["date"], state["selected_time"], state["params"]["party_size"])
            # Prefix with the restaurant name so a bare number can't be confused with party size
            return {"response": f"Selected: {selected['venue_name']}\n\n{card}", "tool_log": []}

        # ── No selection found — check for param-only updates ──
        new_location = _parse_location(msg)
        new_party    = _parse_party_size_explicit(msg)
        new_cuisine  = _parse_cuisine(msg)
        new_date     = _parse_date(msg)
        new_tb       = _parse_time_bucket_explicit(msg)

        params_changed = False
        if new_location and new_location != state["params"]["location"]:
            state["params"]["location"] = new_location
            params_changed = True
        if new_party is not None and new_party != state["params"]["party_size"]:
            state["params"]["party_size"] = new_party
            params_changed = True
        if new_cuisine and new_cuisine != state["params"]["cuisine"]:
            state["params"]["cuisine"] = new_cuisine
            params_changed = True
        if new_date and new_date != state["params"]["date"]:
            state["params"]["date"] = new_date
            params_changed = True
        if new_tb and new_tb != state["params"]["time_bucket"]:
            state["params"]["time_bucket"] = new_tb
            params_changed = True

        if params_changed:
            return _do_recommendations(session_id, user_id, state, tool_log)

        # ── Nothing matched — give a clear in-flow response ────
        if _looks_like_location_attempt(msg, recs):
            candidate = msg.strip().title()
            if not _is_known_location(candidate):
                return _unknown_location_response(candidate)
            state["params"]["location"] = candidate
            return _do_recommendations(session_id, user_id, state, tool_log)

        # Catch "at/in X" patterns where X is an unknown location
        attempted = _extract_location_attempt(msg)
        if attempted and not _is_known_location(attempted):
            return _unknown_location_response(attempted)

        if any(w in msg_low for w in ["availab", "open", "slot", "time slot", "when can"]):
            return {
                "response": (
                    f"All {len(recs)} options above have availability for your requested time. "
                    "Pick one by number or name and I'll show you the full details before booking."
                ),
                "tool_log": [],
            }

        return {
            "response": (
                f"Pick a restaurant by number (1–{len(recs)}) or name. "
                "Or tell me a different neighborhood, party size, or cuisine."
            ),
            "tool_log": [],
        }

    # ── CLARIFYING ─────────────────────────────────────────────
    if state["state"] == "CLARIFYING":
        # If the message is a question or clearly off-topic, answer it without demanding a param
        if _is_question(msg):
            return {"response": _answer_question(msg, state), "tool_log": []}

        # If clearly off-topic AND nothing collected yet, drop back to general chat
        # — but never reset if we're already mid-flow (asking_for is set)
        if not _has_reservation_intent(msg) and not any(state["params"].values()) and not state.get("asking_for"):
            state["state"] = "INITIAL"
            return {"response": _handle_general_chat(msg), "tool_log": []}

        asking = state["asking_for"]
        if asking == "location":
            loc = _parse_location(msg)
            if not loc:
                stripped = msg.strip()
                if len(stripped) > 2 and not any(c in stripped for c in ["?", "!", "."]):
                    candidate = stripped.title()
                    if not _is_known_location(candidate):
                        return _unknown_location_response(candidate)
                    loc = candidate
            if loc:
                state["params"]["location"] = loc
            else:
                return {"response": "Which neighborhood? (e.g. Westwood, West Village, West Loop)", "tool_log": []}
        elif asking == "date":
            date = _parse_date(msg)
            if not date:
                for i, day in enumerate(_DAY_NAMES):
                    if day in msg_low:
                        today = datetime.now()
                        delta = (i - today.weekday()) % 7 or 7
                        date = (today + timedelta(days=delta)).strftime("%Y-%m-%d")
                        break
            if date:
                state["params"]["date"] = date
            else:
                return {"response": "What date? (e.g. \"this Friday\", \"tomorrow\", \"May 20\")", "tool_log": []}

        # Pick up any other intent from this clarifying message
        intent = _parse_intent(msg)
        for key, val in intent.items():
            if val is not None and state["params"].get(key) is None:
                state["params"][key] = val

        missing = _next_missing(state["params"])
        if missing:
            state["asking_for"] = missing
            if missing == "location":
                return {"response": "Which neighborhood are you looking in?", "tool_log": []}
            if missing == "date":
                return {"response": "What date would you like?", "tool_log": []}

        return _do_recommendations(session_id, user_id, state, tool_log)

    # ── INITIAL ────────────────────────────────────────────────
    _BARE_AFFIRMATIVES = {"yes", "yeah", "yep", "yup", "ok", "okay", "sure", "alright", "right", "mhm"}
    if not _has_reservation_intent(msg):
        # Bare "yes" / "ok" with no context → don't call Claude, ask clearly
        if msg_low.strip() in _BARE_AFFIRMATIVES:
            return {"response": "What would you like to book? Just tell me a neighborhood and date.", "tool_log": []}
        if _is_question(msg):
            answer = _answer_question(msg, state)
            if "choose from" not in answer and "change your search" not in answer:
                return {"response": answer, "tool_log": []}
        return {"response": _handle_general_chat(msg), "tool_log": []}

    intent = _parse_intent(msg)
    for key, val in intent.items():
        if val is not None:
            state["params"][key] = val

    missing = _next_missing(state["params"])
    if missing:
        state["state"] = "CLARIFYING"
        state["asking_for"] = missing
        if missing == "location":
            attempted = _extract_location_attempt(msg)
            if attempted and not _is_known_location(attempted):
                return _unknown_location_response(attempted)
            return {"response": "Which neighborhood are you looking in?", "tool_log": []}
        if missing == "date":
            return {"response": "What date would you like?", "tool_log": []}

    return _do_recommendations(session_id, user_id, state, tool_log)


def _do_recommendations(session_id: str, user_id: str, state: dict, tool_log: list) -> dict:
    params = state["params"]
    tool_input = {
        "user_id": user_id,
        "location": params["location"],
        "date": params["date"],
        "time_bucket": params["time_bucket"],
        "party_size": params["party_size"],
        "cuisine": params.get("cuisine"),
    }
    result = tools.get_recommendations(**tool_input)
    tool_log.append({"tool": "get_recommendations", "input": tool_input, "output": result})

    recs = result.get("recommendations", [])
    state["recommendations"] = recs
    state["history_context_applies"] = result.get("history_context_applies", False)
    state["state"] = "SELECTING"

    if not recs:
        location_tried = params["location"]
        state["state"] = "CLARIFYING"
        state["asking_for"] = "location"
        state["params"]["location"] = None
        r = _unknown_location_response(location_tried)
        r["tool_log"] = tool_log
        return r

    try:
        date_fmt = datetime.strptime(params["date"], "%Y-%m-%d").strftime("%A, %B %-d")
    except ValueError:
        date_fmt = params["date"]

    time_label = {"morning": "morning", "afternoon": "afternoon", "evening": "evening", "late_night": "late night"}.get(
        params["time_bucket"], params["time_bucket"]
    )
    cuisine_label = f" {params['cuisine']}" if params.get("cuisine") else ""
    header = f"Here are{cuisine_label} options in {params['location']} for {date_fmt} {time_label} (party of {params['party_size']}):\n\n"

    return {
        "response": header + _fmt_recommendations(recs) + "\n\nReply with a number or restaurant name to select.",
        "tool_log": tool_log,
    }


def reset_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
    db.delete_session(session_id)
