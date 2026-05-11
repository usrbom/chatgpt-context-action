# Action History Pattern Schema

## Overview

Patterns are computed from the user's action history via co-occurrence analysis. Each pattern represents a statistically significant behavioral link between two actions. A pattern **qualifies** (and can be surfaced to the user) only if `support >= 3` and `confidence >= 0.5`.

This file is the template. Fill in `action_history_patterns.json` with real patterns derived from the user's actual action history before labeling the dataset.

---

## Pattern Record Schema

```json
{
  "pattern_id": "string — unique ID, e.g. pattern_001",
  "qualifies": "boolean — true if support >= 3 AND confidence >= 0.5",

  "antecedent": {
    "category": "dining | travel | events | purchases | scheduling",
    "action": "string — exact tool name that triggers this pattern, e.g. book_dining",
    "location_bucket": "string | null — neighborhood or area name, e.g. Riverfront. null if pattern is location-agnostic",
    "time_bucket": "morning | afternoon | evening | late_night | weekend | null — null if time-agnostic",
    "counterparty_type": "business | personal | null — null if not applicable"
  },

  "consequent": {
    "category": "dining | travel | events | purchases | scheduling",
    "action": "string — exact tool name that typically follows",
    "venue_pattern": "string | null — common venue or counterparty name associated with the consequent. null if no consistent venue"
  },

  "statistics": {
    "support": "integer — number of times the antecedent action occurred in the last window_days",
    "co_occurrences": "integer — number of times the consequent followed the antecedent within the session or 3-hour window",
    "confidence": "float — co_occurrences / support, rounded to 2 decimal places",
    "window_days": "integer — lookback window used for computation, default 90"
  },

  "plain_english_template": "string — the exact sentence the agent uses when surfacing this pattern. Format: After {antecedent description}, this user has {consequent description} {confidence*100}% of the time over the last {window_days} days.",

  "last_computed": "ISO-8601 timestamp — when this pattern was last computed from the action history"
}
```

---

## Field Notes

**`location_bucket`** — Use the area or neighborhood name as it appears in the action history payload. Keep consistent across records (e.g., always "Riverfront" not sometimes "the Riverfront" or "Riverfront area").

**`time_bucket` definitions:**
- `morning`: 06:00–11:59
- `afternoon`: 12:00–16:59
- `evening`: 17:00–21:59
- `late_night`: 22:00–05:59
- `weekend`: Saturday or Sunday, any time

**`confidence`** — Always `co_occurrences / support`. Do not round up. A confidence of exactly 0.50 qualifies.

**`plain_english_template`** — This is what D4 and D5 score against. Write it once here and use it verbatim in the agent system prompt. Never rephrase at eval time.

---

## Qualifying Threshold

```
qualifies = (support >= 3) AND (confidence >= 0.5)
```

Non-qualifying patterns must still be stored here — they are used to correctly set `silence_expected: true` for prompts where the antecedent fires but no pattern meets the threshold.
