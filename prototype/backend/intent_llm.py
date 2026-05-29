"""LLM-based intent classifier + slot extractor for SELECTING / CONFIRMING states.

The booking state machine stays deterministic in Python; this module only
turns a free-form user message into a structured intent + slot dict so the
state machine knows what to do next.
"""
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
        _client = Groq()
    return _client


_SYSTEM = (
    "You are an intent classifier for a restaurant booking chat. "
    "Given the current state and a user message, return a single JSON object describing "
    "the user's intent and any extractable slots. Return ONLY the raw JSON — no markdown, no prose."
)


_INTENT_DOC = """
INTENTS (pick exactly one):
- "select"         — user is picking a restaurant (committing to it). slots: {"venue_index": int (1-based), or "venue_name": string}
- "describe_venue" — user wants more info about a specific restaurant WITHOUT committing yet. slots: {"venue_index": int, or "venue_name": string}
- "refresh"        — user wants a different list of restaurants in the same area. slots: {}
- "change_params"  — user is updating search params. slots: any of {location, date, time, party_size, cuisine}
- "filter_price"   — user wants to filter/search by price. slots: {price_min: int, price_max: int} (omit either if open-ended)
- "filter_style"   — user wants a food style. slots: {style_hint: one of ["lighter fare","hearty food","healthy food","casual dining","upscale dining","quick bites","small plates"]}
- "ask_question"   — user is asking why/how/what about the current search state (NOT about a specific venue). slots: {}
- "confirm"        — (CONFIRMING only) user confirms the booking. slots: {}
- "decline"        — (CONFIRMING only) user doesn't want this venue, wants other options. slots: {}
- "cancel"         — user wants to cancel the entire flow. slots: {}
- "chat"           — message is off-topic or pure acknowledgment. slots: {}

COMPOUND-INTENT RULES (read carefully — these matter):
- If the user commits to a venue AND asks for info about it ("I'll do X, tell me more"), choose "select" — the confirmation card always includes the description and popular items.
- If the user names a venue but does NOT commit (e.g., "what's the boiling crab like?", "tell me about #3"), choose "describe_venue".
- If the user just asks general questions ("why this date?", "how is this ranked?"), choose "ask_question".

ANAPHORA RULE:
- If the user says "this one" / "that one" / "it" / "let's do that" AND last_described_venue is set in state,
  treat the venue as last_described_venue. Set venue_name to that exact value.

slot value rules:
- location: a US neighborhood or city name as the user said it (string).
- date: ISO YYYY-MM-DD if you can compute it; otherwise the user's words verbatim.
- time: HH:MM 24-hour string if the user gave a specific time.
- party_size: integer total headcount including the speaker.
- cuisine: one of [Italian, American, Mediterranean, Seafood, New American, Mexican, Asian, French,
  Japanese, Thai, Ethiopian, Indian, Chinese, Korean, Spanish, Greek] if it clearly matches; else string.
- price_min/price_max: integer USD per person.
- venue_name: match against current_options when possible — return the user's words.

Return shape: {"intent": "<intent>", "slots": {...}}
"""


def _state_summary(state: dict) -> str:
    """Compact state context for the prompt — only what matters for intent classification."""
    params = state.get("params", {}) or {}
    recs = state.get("recommendations", []) or []
    selected = state.get("selected_venue") or None

    parts = [f"state={state.get('state')}"]
    for k in ("location", "date", "time_bucket", "party_size", "cuisine", "price_min", "price_max", "style_hint"):
        v = params.get(k)
        if v is not None:
            parts.append(f"{k}={v}")
    if recs:
        names = [f"{i + 1}. {r.get('venue_name')} ({r.get('cuisine')})" for i, r in enumerate(recs)]
        parts.append("current_options=[" + "; ".join(names) + "]")
    if selected:
        parts.append(f"selected={selected.get('venue_name')}")
    last_desc = state.get("last_described_venue")
    if last_desc:
        parts.append(f"last_described_venue={last_desc}")
    return "\n".join(parts)


def extract_intent(state: dict, message: str) -> dict | None:
    """Return {intent, slots} or None on failure (caller falls back to legacy rules)."""
    state_block = _state_summary(state)
    user_block = (
        f"CURRENT STATE:\n{state_block}\n\n"
        f"USER MESSAGE: \"{message}\"\n\n"
        f"{_INTENT_DOC}"
    )
    try:
        response = _get_client().chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user_block},
            ],
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        log.warning("intent_llm: Groq error: %s", e)
        return None

    return _parse_intent_json(raw)


def _parse_intent_json(raw: str) -> dict | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Strip code fences if present
        cleaned = re.sub(r"^```[a-z]*\n?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            log.warning("intent_llm: could not parse JSON: %s", raw[:300])
            return None
    if not isinstance(data, dict) or "intent" not in data:
        return None
    data.setdefault("slots", {})
    if not isinstance(data["slots"], dict):
        data["slots"] = {}
    return data
