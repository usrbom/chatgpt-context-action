#!/usr/bin/env python3
"""
Eval runner — no API key required (uses mock agent).

Test suites:
  Dataset eval  — D1 (tool selection), D2 (parameter accuracy), D4 (history grounding)
                  on 10 dining/normal prompts from the golden dataset.
  Scripted eval — 4-turn booking scenario asserting:
                  (a) correct tool called, (b) history context used,
                  (c) no booking before explicit confirmation, (d) booking logged.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db
import agent
import seed as seed_module

DATASET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "appendix", "eval", "dataset.json")
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "appendix", "eval", "user_history.json")

EVAL_DATE = "2026-05-10"  # dataset date context (Sunday)

G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; B = "\033[1m"; X = "\033[0m"


# ---------------------------------------------------------------------------
# Dimension checks
# ---------------------------------------------------------------------------

def check_d1(tool_calls, expected_tool):
    called = [tc["tool"] for tc in tool_calls]
    if expected_tool in called:
        return True, f"called {expected_tool}"
    return False, f"no tool called" if not called else f"called {called} instead of {expected_tool}"


def check_d2(tool_calls, expected_tool, expected_params):
    call = next((tc for tc in tool_calls if tc["tool"] == expected_tool), None)
    if not call:
        return False, "tool not called"
    mismatches = [
        f"{k}: expected {v!r} got {call['input'].get(k)!r}"
        for k, v in expected_params.items()
        if v is not None and call["input"].get(k) != v
    ]
    return (True, "all params match") if not mismatches else (False, "; ".join(mismatches))


def check_d4(tool_calls, history_context_applies, history_signals, user_history_data):
    call = next((tc for tc in tool_calls if tc["tool"] == "get_recommendations"), None)
    if not call:
        return False, "get_recommendations not called"

    hca = call.get("result", {}).get("history_context_applies", False)
    if history_context_applies and not hca:
        return False, "expected history_context_applies=true, got false"
    if not history_context_applies and hca:
        return False, "expected history_context_applies=false, got true"

    if history_context_applies and history_signals:
        record_map = {r["record_id"]: r["venue_name"] for r in user_history_data.get("restaurant_history", [])}
        expected_venues = {record_map[sid] for sid in history_signals if sid in record_map}
        returned_venues = {r["venue_name"] for r in call.get("result", {}).get("restaurants", [])}
        overlap = expected_venues & returned_venues
        if not overlap:
            return False, f"no expected history venues in results (wanted any of {expected_venues})"
        return True, f"history venues present: {sorted(overlap)}"

    return True, "history_context_applies: false — no fabrication check needed"


# ---------------------------------------------------------------------------
# Dataset eval
# ---------------------------------------------------------------------------

def run_dataset_eval(prompts, user_history_data, n=10):
    dining_normal = [p for p in prompts if p["category"] == "dining" and p["tier"] == "normal"][:n]
    print(f"\n{B}=== Dataset Eval ({len(dining_normal)} dining/normal prompts) ==={X}")

    results = []
    for p in dining_normal:
        pid = p["prompt_id"]
        gt = p["ground_truth"]
        user_id = p.get("user_id", "demo_user_01")
        print(f"\n  [{pid}] {p['prompt_text'][:72]}...")

        try:
            _, tool_calls, _ = agent.run_agent(
                messages=[{"role": "user", "content": p["prompt_text"]}],
                user_id=user_id,
                today=EVAL_DATE,
            )
        except Exception as e:
            print(f"    {R}ERROR: {e}{X}")
            results.append({"id": pid, "d1": False, "d2": False, "d4": False})
            continue

        d1, d1_msg = check_d1(tool_calls, gt["expected_tool"])
        d2, d2_msg = check_d2(tool_calls, gt["expected_tool"], gt["expected_params"])
        d4, d4_msg = check_d4(tool_calls, gt["history_context_applies"], gt.get("history_signals", []), user_history_data)

        ok = d1 and d2 and d4
        badge = f"{G}PASS{X}" if ok else f"{R}FAIL{X}"
        t = lambda b: f"{G}✓{X}" if b else f"{R}✗{X}"
        print(f"    {badge}  D1 {t(d1)} {d1_msg} | D2 {t(d2)} {d2_msg} | D4 {t(d4)} {d4_msg}")
        results.append({"id": pid, "d1": d1, "d2": d2, "d4": d4})

    passed = sum(1 for r in results if r["d1"] and r["d2"] and r["d4"])
    print(f"\n  Result: {passed}/{len(results)} passed")
    return {"passed": passed, "total": len(results)}


# ---------------------------------------------------------------------------
# Scripted booking eval
# ---------------------------------------------------------------------------

def run_scripted_eval(user_id="demo_user_01"):
    print(f"\n{B}=== Scripted Booking Eval (4 turns) ==={X}")

    turns = [
        "Find me Italian restaurants in River North for 2 people this Friday evening",
        "Book Piccolo Sogno at 7:30pm",
        "Yes, go ahead",
        "Jane Smith, 312-555-0100",
    ]

    session_id = "eval_scripted_001"
    history, state = [], None
    assertions = {
        "a_correct_tool_called": False,
        "b_history_context_used": False,
        "c_no_booking_before_confirm": False,
        "d_booking_logged": False,
    }
    booking_before_confirm = False
    initial_events = db.count_events(user_id)

    for i, message in enumerate(turns):
        print(f"\n  Turn {i + 1}: \"{message}\"")
        history.append({"role": "user", "content": message})

        try:
            response_text, tool_calls, state = agent.run_agent(
                messages=list(history), user_id=user_id,
                today=EVAL_DATE, session_id=session_id, state=state,
            )
        except Exception as e:
            print(f"    {R}ERROR: {e}{X}")
            continue

        history.append({"role": "assistant", "content": response_text})
        tools_this_turn = [tc["tool"] for tc in tool_calls]
        print(f"    Tools: {tools_this_turn or '(none)'}")
        print(f"    Agent: {response_text[:80]}...")

        if i == 0:
            rec = [tc for tc in tool_calls if tc["tool"] == "get_recommendations"]
            if rec:
                assertions["a_correct_tool_called"] = True
                assertions["b_history_context_used"] = rec[0].get("result", {}).get("history_context_applies", False)

        if i <= 1 and "book_dining" in tools_this_turn:
            booking_before_confirm = True

    assertions["c_no_booking_before_confirm"] = not booking_before_confirm
    assertions["d_booking_logged"] = db.count_events(user_id) > initial_events

    print(f"\n  Assertions:")
    for key, passed in assertions.items():
        label = key[2:].replace("_", " ")
        print(f"    {'%s✓%s' % (G, X) if passed else '%s✗%s' % (R, X)} ({key[0]}) {label}")

    count = sum(1 for v in assertions.values() if v)
    print(f"\n  Result: {count}/{len(assertions)} assertions passed")
    return {"passed": count, "total": len(assertions)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"{B}Contextual Action Engine — Eval Runner (mock agent, no API key){X}")
    print(f"Date context: {EVAL_DATE}\n")

    db.init_db()
    seed_module.seed()

    with open(DATASET_FILE) as f:
        dataset = json.load(f)
    with open(HISTORY_FILE) as f:
        user_history_data = json.load(f)

    dataset_result = run_dataset_eval(dataset["prompts"], user_history_data, n=10)
    scripted_result = run_scripted_eval()

    print(f"\n{B}=== Summary ==={X}")
    d_pct = dataset_result["passed"] / dataset_result["total"] * 100 if dataset_result["total"] else 0
    s_pct = scripted_result["passed"] / scripted_result["total"] * 100
    print(f"  Dataset eval:  {dataset_result['passed']}/{dataset_result['total']} ({d_pct:.0f}%)")
    print(f"  Scripted eval: {scripted_result['passed']}/{scripted_result['total']} ({s_pct:.0f}%)")

    if d_pct >= 90 and s_pct == 100:
        print(f"\n  {G}{B}Overall: PASS{X}")
    else:
        print(f"\n  {Y}{B}Overall: NEEDS REVIEW{X}")


if __name__ == "__main__":
    main()
