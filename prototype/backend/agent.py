"""Scripted demo agent — no LLM or API key required.

Implements a state machine that drives the full booking flow:
INITIAL → CLARIFYING → SELECTING → CONFIRMING → COLLECTING_NAME → COLLECTING_PHONE → DONE
"""
import re
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
            "party_size": 2,
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


# ── Intent parsing ─────────────────────────────────────────────────────────────

NEIGHBORHOODS: dict[str, str] = {
    "river north": "River North",
    "riverfront": "Riverfront",
    "lincoln park": "Lincoln Park",
    "wicker park": "Wicker Park",
    "the loop": "Loop",
    "west loop": "West Loop",
    "loop": "Loop",
    "downtown": "Loop",
}

CUISINES = ["Italian", "American", "Mediterranean", "Seafood", "New American", "Mexican", "Asian", "French"]

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
    return 2


def _parse_cuisine(text: str) -> str | None:
    low = text.lower()
    for c in CUISINES:
        if c.lower() in low:
            return c
    return None


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
                pass  # "this Tuesday" on Tuesday = today
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
]


def _is_adversarial(text: str) -> bool:
    low = text.lower()
    return any(s in low for s in _ADVERSARIAL)


# ── Main entry point ───────────────────────────────────────────────────────────

def run_turn(session_id: str, user_id: str, user_message: str) -> dict:
    state = _sessions.setdefault(session_id, _new_state())
    msg = user_message.strip()
    msg_low = msg.lower()
    tool_log: list[dict] = []

    # ── Adversarial guard ──────────────────────────────────────
    if _is_adversarial(msg):
        return {
            "response": "I can only help with restaurant bookings. What location and date are you looking for?",
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
        if any(w in msg_low for w in ["confirm", "yes", "book it", "book that", "looks good", "go ahead", "perfect"]):
            state["state"] = "COLLECTING_NAME"
            return {"response": "What name should the reservation be under?", "tool_log": []}
        if any(w in msg_low for w in ["more options", "no", "something else", "different", "other"]):
            recs = state["recommendations"]
            if len(recs) <= 1:
                return {"response": "No other options available for that search. Try a different location or cuisine.", "tool_log": []}
            state["state"] = "SELECTING"
            return {
                "response": "Here are the other options:\n\n" + _fmt_recommendations(recs),
                "tool_log": [],
            }
        # User may be specifying a time
        time_m = re.search(r'\b(\d{1,2}):?(\d{2})?\s*(am|pm)?\b', msg_low)
        if time_m:
            hour = int(time_m.group(1))
            minute = int(time_m.group(2) or 0)
            meridiem = time_m.group(3)
            if meridiem == "pm" and hour < 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
            state["selected_time"] = f"{hour:02d}:{minute:02d}"
            venue = state["selected_venue"]
            response = _fmt_confirmation_card(venue, state["params"]["date"], state["selected_time"], state["params"]["party_size"])
            return {"response": response, "tool_log": []}
        return {"response": "Reply \"confirm\" to book, or \"more options\" for other choices.", "tool_log": []}

    # ── SELECTING ──────────────────────────────────────────────
    if state["state"] == "SELECTING":
        recs = state["recommendations"]
        selected = None

        # By number
        m = re.match(r'^(\d+)$', msg.strip())
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(recs):
                selected = recs[idx]

        # By name (partial match)
        if not selected:
            for r in recs:
                if r["venue_name"].lower() in msg_low or msg_low in r["venue_name"].lower():
                    selected = r
                    break

        if not selected:
            return {
                "response": f"Please choose a number (1–{len(recs)}) or type the restaurant name.",
                "tool_log": [],
            }

        state["selected_venue"] = selected
        state["selected_time"] = _pick_time(selected, state["params"]["time_bucket"])
        state["state"] = "CONFIRMING"
        response = _fmt_confirmation_card(selected, state["params"]["date"], state["selected_time"], state["params"]["party_size"])
        return {"response": response, "tool_log": []}

    # ── CLARIFYING ─────────────────────────────────────────────
    if state["state"] == "CLARIFYING":
        asking = state["asking_for"]
        if asking == "location":
            loc = _parse_location(msg)
            if not loc:
                # Try treating the whole message as a location
                loc = msg.strip().title() if len(msg.strip()) > 2 else None
            if loc:
                state["params"]["location"] = loc
            else:
                return {"response": "Which neighborhood? (e.g. River North, West Loop, Lincoln Park)", "tool_log": []}
        elif asking == "date":
            date = _parse_date(msg)
            if not date:
                # Check if it's just a day name
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

        # Also pick up any other intent from this clarifying message
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

        # All params ready — get recommendations
        return _do_recommendations(session_id, user_id, state, tool_log)

    # ── INITIAL ────────────────────────────────────────────────
    intent = _parse_intent(msg)
    for key, val in intent.items():
        if val is not None:
            state["params"][key] = val

    missing = _next_missing(state["params"])
    if missing:
        state["state"] = "CLARIFYING"
        state["asking_for"] = missing
        if missing == "location":
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
        state["state"] = "INITIAL"
        return {
            "response": (
                f"No restaurants found in {params['location']} matching your criteria. "
                "Try a different neighborhood or cuisine."
            ),
            "tool_log": tool_log,
        }

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
