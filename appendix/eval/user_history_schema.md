# User History Schema

## Overview

The recommendation engine ranks restaurant suggestions using the user's behavioral history — not stated preferences. Two data structures drive this, both **derived and computed** from the raw booking events stored in SQLite (see Section 6 of `docs/source_of_truth.md`). They are not stored directly by users — the system builds and updates them after every `log_action` call.

1. **Restaurant History Records** — one record per unique venue visited, aggregated across all raw booking events within the lookback window. These are what `retrieve_behavioral_context` queries to rank results.
2. **Preference Signals** — derived aggregates across all history records. Used as a fallback when no venue-level history exists for the specific location or time being queried.

This file is the schema template. `user_history.json` contains the seeded demo data for `demo_user_01` used in eval labeling.

---

## time_bucket and day_type Definitions

**`time_bucket`:**
- `morning`: 06:00–11:59
- `afternoon`: 12:00–16:59
- `evening`: 17:00–21:59
- `late_night`: 22:00–05:59

**`day_type`:**
- `weekday`: Monday–Friday
- `weekend`: Saturday or Sunday

**Natural language → `time_bucket` inference (used by the agent when parsing user intent):**

| User says | Resolves to |
|---|---|
| "lunch", "midday" | `afternoon` |
| "dinner", "evening", "tonight", "night" | `evening` |
| "brunch", "breakfast", "morning" | `morning` |
| "late night", "late dinner", "after 10" | `late_night` |

---

## 1. Restaurant History Record

One record per unique venue visited. If a user visited the same restaurant 5 times, that is one record with `visit_count: 5`, not 5 records.

```json
{
  "record_id": "string — unique ID, e.g. RH_001",
  "user_id": "string",
  "venue_name": "string — exact restaurant name as it appears on OpenTable",
  "venue_id": "string | null — OpenTable or third-party ID if available",
  "location_bucket": "string — neighborhood area, e.g. River North, Riverfront, Wicker Park",
  "cuisine": "string — cuisine type, e.g. Italian, American, Japanese, Mediterranean",
  "typical_time_bucket": "morning | afternoon | evening | late_night — modal time_bucket across visits",
  "typical_day_type": "weekday | weekend | null — null if visits are evenly split",
  "visit_count": "integer — total visits within window_days",
  "last_visited": "YYYY-MM-DD — date of most recent visit",
  "party_size_avg": "float — average party size across visits, rounded to 1 decimal",
  "counterparty_type": "business | personal | null — null if mixed or unknown",
  "window_days": "integer — lookback window, default 90"
}
```

### Field notes

**`location_bucket`** — Use the exact neighborhood name consistently across all records. "River North" not "the River North" or "RiverNorth".

**`venue_name`** — Must match the name as it appears in the third-party booking system. This is what D4 checks against — if the agent cites a venue not present in the relevant history records, it is a fabrication.

**`typical_time_bucket`** — Modal time_bucket across all visits to this venue. Used to surface contextually appropriate recommendations (e.g., a venue the user only visits in the evening should not rank highly for a lunch query).

**`visit_count`** — Primary ranking signal. Higher visit_count = stronger preference. Ties broken by `last_visited` (more recent wins).

---

## 2. Preference Signals

Derived from the restaurant history records. Computed once and stored alongside the records. Re-computed whenever new records are added.

```json
{
  "computed_at": "ISO-8601 timestamp",
  "window_days": "integer — lookback window, default 90",

  "cuisines": [
    {
      "cuisine": "string",
      "visit_count": "integer — total visits across all venues of this cuisine",
      "rank": "integer — 1 = most visited"
    }
  ],

  "neighborhoods": [
    {
      "location_bucket": "string",
      "visit_count": "integer — total visits across all venues in this neighborhood",
      "rank": "integer — 1 = most visited"
    }
  ],

  "time_preferences": [
    {
      "time_bucket": "morning | afternoon | evening | late_night",
      "visit_count": "integer",
      "rank": "integer"
    }
  ],

  "day_preferences": [
    {
      "day_type": "weekday | weekend",
      "visit_count": "integer",
      "rank": "integer"
    }
  ]
}
```

### Ranking rule

Within each preference array, records are sorted by `visit_count` descending. `rank: 1` is the most visited. Ties are broken by recency of the most recent visit in that group.

---

## How `retrieve_behavioral_context` uses this schema

When the agent calls `retrieve_behavioral_context` (step 2 of the agent loop), the tool:

1. Filters `restaurant_history` records where `location_bucket` exactly matches the query location AND `typical_time_bucket` matches the query `time_bucket` AND cuisine matches (if a filter was provided)
2. If matching records exist → sets `history_context_applies: true` and returns them ranked by `visit_count` then `last_visited`
3. If no records match → sets `history_context_applies: false` and returns `preference_signals` only as a fallback

The agent uses the returned records to re-rank results from `search_restaurants`. It must not claim personalization ("you usually visit…") when `history_context_applies: false`.

---

## How `history_signals` in ground truth maps to this schema

The `history_signals` field in each dataset prompt is a list of `record_id` values from the restaurant history records. It specifies which records the agent should have retrieved and used to inform its recommendations for that prompt.

D4 (History Grounding) checks: for each recommendation the agent surfaces, can it be traced to a record in `history_signals`? If the agent recommends a venue not in those records, or claims the user "frequently visits" a place not represented in those records, D4 fails.

When `history_context_applies: false`, `history_signals` is `[]` and D4 checks that the agent makes no history claims at all.
