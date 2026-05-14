"""
Mock agent — no API key required.
Uses a rule-based state machine that mirrors the 6-step booking flow.
Calls the same tools (get_recommendations, book_dining, show_patterns, forget_me)
and returns the same (text, tool_calls, state) interface.
"""
import re
from datetime import date as date_type, timedelta
import tools as tool_module

LOCATIONS = ["River North", "West Loop", "Wicker Park", "Lincoln Park", "Riverfront", "Loop"]
CUISINES = ["Italian", "American", "Mexican", "Mediterranean", "Seafood", "New American", "Japanese"]

TIME_KEYWORDS = {
    "morning":   ["breakfast", "brunch", "morning"],
    "afternoon": ["afternoon", "lunch", "midday", "noon"],
    "evening":   ["evening", "dinner", "tonight", "supper"],
    "late_night": [],  # handled separately below
}

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAY_DOW = {d: i for i, d in enumerate(DAYS)}


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _parse_location(text: str):
    tl = text.lower()
    for loc in LOCATIONS:
        if loc.lower() in tl:
            return loc
    import re
    m = re.search(r"\b(?:near|in|around)\s+([a-z0-9\s]+?)(?:[,\.]|$)", tl)
    if m:
        return m.group(1).strip().title()
    return None


def _parse_time_bucket(text: str):
    tl = text.lower()
    if "late night" in tl or "late-night" in tl or "after 10" in tl:
        return "late_night"
    # Check "night" separately — covers "Friday night" but not "late night" (handled above)
    for bucket, keywords in TIME_KEYWORDS.items():
        for kw in keywords:
            if kw in tl:
                return bucket
    if "night" in tl:
        return "evening"
    return None


def _parse_party_size(text: str):
    tl = text.lower()
    word_nums = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    patterns = [
        r'(?:for|party\s+of|table\s+for|group\s+of)\s+(\w+)',
        r'(\w+)\s+(?:people|guests|persons?|of\s+us)',
    ]
    for pattern in patterns:
        m = re.search(pattern, tl)
        if m:
            val = m.group(1).strip()
            if val.isdigit():
                return int(val)
            if val in word_nums:
                return word_nums[val]
    if re.search(r'\bjust\s+(?:me|myself)\b', tl):
        return 1
    if re.search(r'\bme\s+and\s+(?:my\s+)?\w+\b', tl):
        return 2
    return None


def _parse_date(text: str, today_str: str):
    today = date_type.fromisoformat(today_str)
    tl = text.lower()

    if "today" in tl:
        return today_str
    if "tomorrow" in tl:
        return (today + timedelta(days=1)).isoformat()

    for day_name in DAYS:
        if day_name in tl:
            target_dow = DAY_DOW[day_name]
            delta = (target_dow - today.weekday()) % 7
            if delta == 0:
                delta = 7
            if "next" in tl:
                delta = delta if delta > 7 else delta + 7
            return (today + timedelta(days=delta)).isoformat()

    m = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
    if m:
        return m.group(1)
    return None


def _parse_cuisine(text: str):
    tl = text.lower()
    for c in CUISINES:
        if c.lower() in tl:
            return c
    return None


def _parse_time_str(text: str):
    m = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b', text, re.IGNORECASE)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2)) if m.group(2) else 0
    ampm = (m.group(3) or "").lower()
    if ampm == "pm" and hour < 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0
    elif not ampm and 1 <= hour <= 9:
        hour += 12  # assume PM for single-digit ambiguous times
    return f"{hour:02d}:{minute:02d}"


def _parse_phone(text: str):
    m = re.search(r'[\d\-\.\(\)\s]{10,}', text)
    if m:
        digits = re.sub(r'\D', '', m.group())
        if len(digits) >= 10:
            return digits
    return None


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def _fmt_recommendations(restaurants: list) -> str:
    lines = ["Here are some options:\n"]
    for i, r in enumerate(restaurants, 1):
        times = ", ".join(r["available_times"][:4])
        lines.append(f"**{i}. {r['venue_name']}** — {r['cuisine']} · ~${r['estimated_cost_per_person']}/person")
        lines.append(f"   {r['address']}")
        lines.append(f"   Available: {times}\n")
    lines.append("Which one would you like, and what time?")
    return "\n".join(lines)


def _fmt_confirmation(venue: dict, date_str: str, time_str: str, party_size: int) -> str:
    return (
        f"**Reservation Summary**\n"
        f"- **Restaurant:** {venue['venue_name']}, {venue['address']}\n"
        f"- **Cuisine:** {venue['cuisine']} · ~${venue['estimated_cost_per_person']}/person\n"
        f"- **Date:** {date_str} · **Time:** {time_str} · **Party:** {party_size}\n\n"
        f"Shall I confirm this booking?"
    )


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------

def _fresh_state() -> dict:
    return {
        "step": "idle",
        "params": {},
        "candidates": [],
        "selected": None,
        "time": None,
        "confirm_forget": False,
    }


def run_agent(
    messages: list,
    user_id: str = "demo_user_01",
    today: str = None,
    session_id: str = "default",
    state: dict = None,
) -> tuple:
    if today is None:
        today = date_type.today().isoformat()
    if state is None:
        state = _fresh_state()

    last_user = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            content = msg["content"]
            last_user = content if isinstance(content, str) else ""
            break

    tl = last_user.lower()
    log = []

    # ---- Privacy triggers (work from any step) ----
    if any(kw in tl for kw in ["show my patterns", "what do you know", "show patterns"]):
        result = tool_module.show_patterns(user_id)
        log.append({"tool": "show_patterns", "input": {"user_id": user_id}, "result": result})
        if not result["restaurant_history"]:
            return "No behavioral history on record.", log, state
        lines = ["**Your behavioral history:**\n"]
        for r in result["restaurant_history"][:6]:
            lines.append(f"- {r['venue_name']} ({r['cuisine']}, {r['location_bucket']}) — {r['visit_count']} visit(s)")
        return "\n".join(lines), log, state

    if any(kw in tl for kw in ["forget me", "delete my history", "forget everything"]):
        if state.get("confirm_forget"):
            result = tool_module.forget_me(user_id)
            log.append({"tool": "forget_me", "input": {"user_id": user_id}, "result": result})
            new_state = _fresh_state()
            return result["message"], log, new_state
        state["confirm_forget"] = True
        return "This will permanently delete all your behavioral history. Are you sure? Reply 'yes, forget me' to confirm.", log, state

    if state.get("confirm_forget"):
        if any(kw in tl for kw in ["yes", "sure", "confirm", "ok"]):
            result = tool_module.forget_me(user_id)
            log.append({"tool": "forget_me", "input": {"user_id": user_id}, "result": result})
            new_state = _fresh_state()
            return result["message"], log, new_state
        state["confirm_forget"] = False

    step = state["step"]
    params = state["params"]

    # ---- STEP: collecting_details — waiting for name + phone ----
    if step == "collecting_details":
        phone = _parse_phone(last_user)
        name_text = re.sub(r'[\d\-\.\(\)\s]{10,}', '', last_user).strip().strip(',').strip()
        if not name_text:
            name_text = last_user.split(',')[0].strip()

        if not phone or not name_text or name_text == last_user.strip():
            return "Please provide both a name and phone number (e.g. Jane Smith, 312-555-0100).", log, state

        selected = state["selected"]
        result = tool_module.book_dining(
            venue_id=selected["venue_id"],
            venue_name=selected["venue_name"],
            date=params["date"],
            time=state["time"],
            party_size=params.get("party_size", 1),
            counterparty_name=name_text,
            counterparty_phone=phone,
            user_id=user_id,
            session_id=session_id,
        )
        log.append({"tool": "book_dining", "input": {
            "venue_id": selected["venue_id"], "venue_name": selected["venue_name"],
            "date": params["date"], "time": state["time"],
            "party_size": params.get("party_size", 1),
            "counterparty_name": name_text, "counterparty_phone": phone,
        }, "result": result})

        if result["booking_confirmed"]:
            state["step"] = "done"
            return (
                f"Booking confirmed!\n\n"
                f"**Confirmation ID:** `{result['confirmation_id']}`\n"
                f"- **Restaurant:** {result['venue_name']}\n"
                f"- **Date:** {result['date']} · **Time:** {result['time']} · **Party:** {result['party_size']}\n\n"
                f"Enjoy your meal."
            ), log, state
        else:
            state["step"] = "recommending"
            return f"{result['error_message']} Try a different time or visit opentable.com.", log, state

    # ---- STEP: confirming — waiting for yes/no ----
    if step == "confirming":
        if any(kw in tl for kw in ["yes", "confirm", "go ahead", "book it", "sounds good", "perfect", "do it", "sure"]):
            state["step"] = "collecting_details"
            return "What name and phone number should I put the reservation under?", log, state
        elif any(kw in tl for kw in ["no", "cancel", "different", "other", "back", "more options", "something else"]):
            state["step"] = "recommending"
            return _fmt_recommendations(state["candidates"]) if state["candidates"] else "What would you like instead?", log, state
        else:
            selected = state.get("selected")
            if selected:
                return _fmt_confirmation(selected, params["date"], state["time"], params.get("party_size", 1)), log, state
            return "Shall I confirm this booking? (yes / no)", log, state

    # ---- STEP: recommending — waiting for venue + time selection ----
    if step == "recommending":
        candidates = state.get("candidates", [])
        new_time = _parse_time_str(last_user)

        selected = None
        for i, r in enumerate(candidates):
            if (str(i + 1) in last_user
                    or r["venue_name"].lower() in tl
                    or r["venue_name"].split()[0].lower() in tl):
                selected = r
                break

        if selected and new_time:
            state["selected"] = selected
            state["time"] = new_time
            state["step"] = "confirming"
            return _fmt_confirmation(selected, params["date"], new_time, params.get("party_size", 1)), log, state
        elif selected:
            state["selected"] = selected
            times = ", ".join(selected["available_times"][:5])
            return f"What time for {selected['venue_name']}? Available: {times}", log, state
        elif new_time and state.get("selected"):
            state["time"] = new_time
            state["step"] = "confirming"
            return _fmt_confirmation(state["selected"], params["date"], new_time, params.get("party_size", 1)), log, state
        else:
            return _fmt_recommendations(candidates), log, state

    # ---- STEP: idle / collecting — gather params then search ----
    if not params.get("location"):
        params["location"] = _parse_location(last_user)
    if not params.get("time_bucket"):
        params["time_bucket"] = _parse_time_bucket(last_user)
    if not params.get("date"):
        params["date"] = _parse_date(last_user, today)
    if not params.get("party_size"):
        params["party_size"] = _parse_party_size(last_user)
    if not params.get("cuisine"):
        params["cuisine"] = _parse_cuisine(last_user)
    state["params"] = params

    if not params.get("location"):
        state["step"] = "collecting"
        return "Which area or neighborhood are you looking to eat in?", log, state
    if not params.get("date"):
        state["step"] = "collecting"
        return "What date are you looking for?", log, state
    if not params.get("time_bucket"):
        state["step"] = "collecting"
        return "What time of day? (morning, lunch, dinner, or late night)", log, state

    if not params.get("party_size"):
        params["party_size"] = 1

    result = tool_module.get_recommendations(
        location=params["location"],
        date=params["date"],
        time_bucket=params["time_bucket"],
        party_size=params["party_size"],
        cuisine=params.get("cuisine"),
        user_id=user_id,
    )
    log.append({"tool": "get_recommendations", "input": {
        "location": params["location"], "date": params["date"],
        "time_bucket": params["time_bucket"], "party_size": params["party_size"],
        "cuisine": params.get("cuisine"),
    }, "result": result})

    if not result["restaurants"]:
        state["step"] = "idle"
        state["params"] = {}
        return (
            f"No restaurants found in {params['location']} for {params['time_bucket']}. "
            f"Try a different neighborhood or time of day."
        ), log, state

    state["step"] = "recommending"
    state["candidates"] = result["restaurants"]
    return _fmt_recommendations(result["restaurants"]), log, state
