from __future__ import annotations

import json
import logging
import re

log = logging.getLogger(__name__)

_client = None

def _get_client():
    global _client
    if _client is None:
        from groq import Groq
        _client = Groq()  # reads GROQ_API_KEY from environment
    return _client

_REQUIRED_FIELDS = {
    "venue_id", "venue_name", "address", "cuisine",
    "estimated_cost_per_person", "rating", "available_times", "location_bucket",
}

_TIME_LABELS = {
    "09:00": "breakfast or brunch",
    "13:00": "lunch",
    "19:00": "dinner",
    "22:00": "late-night dining",
}

_TIME_SLOT_DEFAULTS = {
    "09:00": ["08:30", "09:00", "09:30", "10:00", "10:30"],
    "13:00": ["12:00", "12:30", "13:00", "13:30", "14:00"],
    "19:00": ["18:00", "18:30", "19:00", "19:30", "20:00"],
    "22:00": ["21:30", "22:00", "22:30", "23:00"],
}


def search_restaurants(
    location: str,
    date: str,
    time: str,
    party_size: int,
    cuisine: str | None = None,
    history_venue_names: list[str] | None = None,
    exclude_venue_names: list[str] | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    style_hint: str | None = None,
) -> list[dict]:
    """Ask OpenAI for real restaurants. Returns same schema as mock_api, or [] on failure."""
    prompt = _build_prompt(location, date, time, party_size, cuisine, history_venue_names or [], exclude_venue_names or [], price_min, price_max, style_hint)
    raw = _call_openai(prompt)
    if raw is None:
        return []
    results = _parse(raw, location, time)
    if not results:
        log.warning("claude_search: parse returned 0 venues. Raw output:\n%s", raw[:500])
    return results


def _build_prompt(
    location: str,
    date: str,
    time: str,
    party_size: int,
    cuisine: str | None,
    history_names: list[str],
    exclude_names: list[str],
    price_min: int | None = None,
    price_max: int | None = None,
    style_hint: str | None = None,
) -> str:
    time_label = _TIME_LABELS.get(time, "dinner")
    cuisine_clause = f" serving {cuisine} cuisine" if cuisine else ""
    style_clause = f" ({style_hint})" if style_hint else ""

    if price_min and price_max:
        price_clause = f" in the ${price_min}–${price_max}/person price range"
    elif price_min:
        price_clause = f" costing over ${price_min}/person"
    elif price_max:
        price_clause = f" costing under ${price_max}/person"
    else:
        price_clause = ""

    history_clause = ""
    if history_names:
        names_str = ", ".join(f'"{n}"' for n in history_names)
        history_clause = (
            f"\n\nIf any of these venue names are real restaurants that exist in {location}, "
            f"include them by their exact name: {names_str}"
        )

    exclude_clause = ""
    if exclude_names:
        names_str = ", ".join(f'"{n}"' for n in exclude_names)
        exclude_clause = f"\n\nDo NOT include any of these restaurants: {names_str}"

    slots_example = json.dumps(_TIME_SLOT_DEFAULTS.get(time, ["18:00", "19:00", "20:00"]))

    return (
        f"Return a JSON array of 5 to 8 real restaurants in {location} "
        f"suitable for {time_label} for a party of {party_size}{cuisine_clause}{style_clause}{price_clause}.{history_clause}{exclude_clause}\n\n"
        f"Each object must have exactly these fields:\n"
        f'  "venue_id": a short unique slug (e.g. "vn_abc123"),\n'
        f'  "venue_name": exact restaurant name,\n'
        f'  "address": full street address,\n'
        f'  "cuisine": cuisine type,\n'
        f'  "estimated_cost_per_person": integer USD with no dollar sign (e.g. 55),\n'
        f'  "rating": float between 4.0 and 5.0 (e.g. 4.7),\n'
        f'  "available_times": JSON array of HH:MM strings like {slots_example},\n'
        f'  "location_bucket": "{location}",\n'
        f'  "description": one short sentence (10-18 words) on vibe / what makes it notable,\n'
        f'  "popular_items": JSON array of 2-3 signature menu items (e.g. ["Truffle Pizza", "Burrata"])\n\n'
        f"Return ONLY the raw JSON array. No explanation, no markdown, no code fences, no trailing text."
    )


def _call_openai(prompt: str) -> str | None:
    try:
        response = _get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.warning("claude_search: OpenAI API error: %s", e)
    return None


def _to_int(val: object, default: int = 50) -> int:
    try:
        return int(str(val).replace("$", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def _to_float(val: object, default: float = 4.5) -> float:
    try:
        return float(str(val).replace("$", "").strip())
    except (TypeError, ValueError):
        return default


def _extract_json_array(raw: str) -> list | None:
    # Try the whole response first
    stripped = raw.strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences and retry
    stripped = re.sub(r"^```[a-z]*\n?", "", stripped, flags=re.MULTILINE)
    stripped = re.sub(r"\n?```$", "", stripped, flags=re.MULTILINE)
    try:
        parsed = json.loads(stripped.strip())
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    # Extract first [...] block by bracket scanning
    start = raw.find("[")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(raw[start:], start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _parse(raw: str, location: str, time: str) -> list[dict]:
    items = _extract_json_array(raw)
    if items is None:
        return []

    default_slots = _TIME_SLOT_DEFAULTS.get(time, ["18:00", "19:00", "20:00"])
    valid = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if not _REQUIRED_FIELDS.issubset(item.keys()):
            missing = _REQUIRED_FIELDS - item.keys()
            log.debug("claude_search: venue missing fields %s, skipping", missing)
            continue
        item["estimated_cost_per_person"] = _to_int(item["estimated_cost_per_person"])
        item["rating"] = _to_float(item["rating"])
        if not isinstance(item.get("available_times"), list) or not item["available_times"]:
            item["available_times"] = default_slots
        item["location_bucket"] = location
        item.setdefault("description", "")
        if not isinstance(item.get("popular_items"), list):
            item["popular_items"] = []
        valid.append(item)

    return valid
