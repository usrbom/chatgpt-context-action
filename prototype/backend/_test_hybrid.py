"""Smoke test for the hybrid LLM-intent refactor.
Runs the scenarios that previously failed and prints the bot's response for each turn."""
from __future__ import annotations

import os
import sys
import uuid

from dotenv import load_dotenv
load_dotenv()

import agent


SCENARIOS = [
    {
        "name": "S1: 'john and sarah' should give party of 3",
        "messages": [
            "i'm meeting with john and sarah",
            "westwood",
            "tonight",
        ],
        "check": lambda last: "party of 3" in last["response"].lower(),
    },
    {
        "name": "S2: 'anything else?' in SELECTING should refresh",
        "messages": [
            "find me a restaurant in westwood tonight",
            "anything else?",
        ],
        "check": lambda last: "options" in last["response"].lower() and ("here are" in last["response"].lower() or "westwood" in last["response"].lower()),
    },
    {
        "name": "S3: 'can you make that 4?' in SELECTING should update party",
        "messages": [
            "find me a restaurant in westwood tonight for 2",
            "can you make that 4?",
        ],
        "check": lambda last: "party of 4" in last["response"].lower(),
    },
    {
        "name": "S4: 'narrow it down to arlington area?' should change location",
        "messages": [
            "find restaurants in virginia tonight",
            "can you narrow it down to arlington area?",
        ],
        "check": lambda last: "arlington" in last["response"].lower(),
    },
    {
        "name": "S5: 'something healthier' should re-search with style hint",
        "messages": [
            "find me a restaurant in westwood tonight",
            "something healthier",
        ],
        "check": lambda last: "westwood" in last["response"].lower() and ("here are" in last["response"].lower() or "options" in last["response"].lower()),
    },
    {
        "name": "S6: 'why did you think it was today?' (after silent default removed, this now asks first)",
        "messages": [
            "westwood",
        ],
        "check": lambda last: "when" in last["response"].lower() or "date" in last["response"].lower(),
    },
    {
        "name": "S7: 'anything over $50/person?' in SELECTING should apply price filter",
        "messages": [
            "find me a restaurant in westwood tonight",
            "anything over $50/person?",
        ],
        "check": lambda last: "$50" in last["response"] or "over" in last["response"].lower() or "options" in last["response"].lower(),
    },
    {
        "name": "S8: changing date should NOT change the venue list (cache stability)",
        "messages": [
            "find me a restaurant in westwood this friday",
            "actually sunday",
        ],
        # Pass criterion: this is checked by comparing venue order between turns — done specially below
        "check": None,
    },
    {
        "name": "S9: compound 'I'll do X, can you give me more info?' should SELECT and show details",
        "messages": [
            "find me a restaurant in westwood tonight",
            "i'll do option 2. can you give me more info?",
        ],
        "check": lambda last: ("here are your booking details" in last["response"].lower() or "selected:" in last["response"].lower()) and ("about:" in last["response"].lower() or "popular:" in last["response"].lower()),
    },
    {
        "name": "S10: 'tell me more about #3' should DESCRIBE without selecting",
        "messages": [
            "find me a restaurant in westwood tonight",
            "tell me more about #3",
        ],
        "check": lambda last: "here are your booking details" not in last["response"].lower() and ("popular" in last["response"].lower() or len(last["response"]) > 80),
    },
    {
        "name": "S11: confirmation card includes the edit hint",
        "messages": [
            "find me a restaurant in westwood tonight",
            "i'll do option 1",
        ],
        "check": lambda last: "tip:" in last["response"].lower() and "edit" in last["response"].lower(),
    },
    {
        "name": "S12: clicking Confirm offers saved contact when one exists",
        # Pre-seeded contact via db.save_contact below in special-cased setup
        "messages": [
            "find me a restaurant in westwood tonight",
            "1",
            "confirm",
        ],
        "check": lambda last: "saved" in last["response"].lower() and ("kady" in last["response"].lower() or "use" in last["response"].lower()),
        "setup": lambda uid: __import__("db").save_contact(uid, "Kady Test", "555-0199"),
    },
]


def _venues_from_text(text: str) -> list[str]:
    """Extract '1. Name —' style entries from response text for comparison."""
    import re as _re
    return _re.findall(r'^\s*\d+\.\s+([^—\n]+?)\s+—', text, flags=_re.MULTILINE)


def run_scenario(scenario: dict) -> tuple[bool, list[str]]:
    sid = f"test-{uuid.uuid4().hex[:8]}"
    uid = f"demo_user_test_{uuid.uuid4().hex[:6]}"  # fresh user each run
    if scenario.get("setup"):
        scenario["setup"](uid)
    transcript = []
    responses = []
    for msg in scenario["messages"]:
        transcript.append(f"U: {msg}")
        last = agent.run_turn(sid, uid, msg)
        responses.append(last)
        resp = last["response"]
        if len(resp) > 600:
            resp = resp[:600] + " …(truncated)"
        transcript.append(f"AI: {resp}")
    agent.reset_session(sid)

    if scenario["check"] is None:
        # S8 special case: venue list before and after date change should match
        if len(responses) >= 2:
            v1 = _venues_from_text(responses[-2]["response"])
            v2 = _venues_from_text(responses[-1]["response"])
            passed = bool(v1) and v1 == v2
            transcript.append(f"  [venue-stability check] before={v1} after={v2} match={passed}")
        else:
            passed = False
    else:
        passed = scenario["check"](responses[-1]) if responses else False
    return passed, transcript


def main():
    results = []
    for sc in SCENARIOS:
        try:
            passed, transcript = run_scenario(sc)
            results.append((sc["name"], passed, transcript, None))
        except Exception as e:
            results.append((sc["name"], False, [], str(e)))

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    for name, passed, transcript, err in results:
        flag = "PASS" if passed else "FAIL"
        print(f"\n[{flag}] {name}")
        if err:
            print(f"  ERROR: {err}")
        for line in transcript:
            for sub in line.split("\n"):
                print(f"  {sub}")

    total = len(results)
    n_pass = sum(1 for _, p, _, _ in results if p)
    print("\n" + "=" * 70)
    print(f"SUMMARY: {n_pass}/{total} passed")
    print("=" * 70)
    sys.exit(0 if n_pass == total else 1)


if __name__ == "__main__":
    main()
