# ChatGPT In-Chat Restaurant Booking — Prototype Spec

## 1. Overview

### Problem
ChatGPT users must leave the app to complete restaurant bookings after their conversations. They ask where to eat, then open OpenTable. Every context switch breaks continuity and hands the high-intent moment to a competitor.

### Goal
Allow users to search, select, and book a restaurant entirely within ChatGPT — no app switching, no external redirects.

### Target User
Urban professionals aged 25–45, daily ChatGPT users who want to complete real-world tasks without leaving the interface.

### Success Metric
User completes a booking end-to-end (search → select → confirm) within a single chat conversation.

---

## 2. Scope

**In scope**
- Chat interface for restaurant booking
- Clarify missing info before searching; smart defaults reduce questions asked
- Present restaurant options retrieved from OpenAI (live) or mock data (fallback)
- Any US city or neighborhood — OpenAI handles locations not in mock data
- Preference pre-filling from booking history via RAG
- User confirmation before any booking action
- Booking confirmation displayed in chat

**Out of scope**
- Hotels, flights, events, or any non-restaurant booking
- Calendar integration
- Post-booking recommendations
- Real payment processing
- Automated actions without user confirmation

---

## 3. Agent System Prompt

```
You are a restaurant booking assistant inside ChatGPT. Your job is to help
users find and book a restaurant — entirely within this chat.

On every user turn, follow this loop:

1. INTENT. Identify the parameters needed to search: location, date, time,
   party size, and any cuisine or budget preference. If a required parameter
   is missing and cannot be safely inferred, ask 1 clarifying question at a
   time. Do not ask multiple questions at once.

2. BEHAVIORAL CONTEXT. Before searching, call retrieve_behavioral_context with
   the user's id and the parsed intent. Use retrieved patterns to rank results —
   do not surface them as suggestions or recommendations. Only use patterns that
   are grounded in actual past behavior.

3. SEARCH. Call the restaurant search tool. Return the top 3–5 options, ranked
   by behavioral relevance where applicable.

4. CONFIRM. Before executing any booking, show a confirmation card with all
   relevant details and wait for explicit user approval.

5. BOOK. Execute the booking only after confirmation. Collect any remaining
   required personal details (name, contact) at this step — do not ask earlier.

6. LOG. After each successful booking, call log_action with the full payload
   and outcome.

Rules:
- Never book without explicit user confirmation.
- Never fabricate behavioral patterns. If retrieve_behavioral_context returns
  nothing relevant, rank results by rating.
- Ask only for personal information (name, phone) when required to complete
  the booking — not before.
- If a tool fails, explain what happened in plain language and offer one
  recovery path (e.g. a link to OpenTable or Yelp).
- No technical terms or error codes in user-facing messages.
- Tone: calm, efficient, no filler phrases ("Great choice!", "Absolutely!").
```

---

## 4. User Journey

1. User requests a restaurant booking in chat (e.g. "Book me a table for 2 this Friday near downtown")
2. Agent identifies intent and asks for any missing required details — location, date, time, party size (one question at a time)
3. Agent validates inputs, then searches via the (mocked) restaurant API
4. Agent presents 3–5 restaurant options, ranked by behavioral preference where applicable
5. User selects an option
6. Agent shows a confirmation card and waits for explicit approval
7. Agent collects any remaining required personal details (name, phone number)
8. User confirms — agent completes the booking
9. Agent displays booking confirmation in chat

---

## 5. Confirmation Card (UI)

Before any booking is executed, display a card containing:

- Restaurant name and address
- Cuisine style and estimated cost per person
- Date, time, party size
- Buttons: **[ Confirm Booking ]** | **[ More Options ]**

---

## 6. Data Requirements

### User Input
- Booking details: location, date, time, party size, and optionally cuisine or budget — collected before search
- Personal info: name and phone number — collected only at confirmation step

### Internal Database (SQLite)
- **Booking history**: past completed restaurant bookings — used by RAG to rank options
- **Chat history**: past conversations — used to infer preferences (e.g. cuisine type, price range, neighborhood)
- Schema per record:
```json
{
  "event_id": "uuid",
  "user_id": "string",
  "timestamp": "ISO-8601",
  "category": "dining",
  "action": "book_restaurant",
  "payload": {
    "title": "string",
    "location": { "name": "string", "lat": "number", "lon": "number" },
    "time": "ISO-8601",
    "counterparty": "string (restaurant name)",
    "amount": "number (estimated cost per person)",
    "category_tags": ["string (e.g. Italian, date-night, loud)"]
  },
  "outcome": "confirmed | failed | cancelled",
  "session_id": "string"
}
```

**Do not store raw personal data** (name, phone number) in the database.

---

### time_bucket and day_type Definitions

Used in both raw events and derived records. Must be applied consistently everywhere.

| `time_bucket` | Time range |
|---|---|
| `morning` | 06:00–11:59 |
| `afternoon` | 12:00–16:59 |
| `evening` | 17:00–21:59 |
| `late_night` | 22:00–05:59 |

| `day_type` | Definition |
|---|---|
| `weekday` | Monday–Friday |
| `weekend` | Saturday or Sunday |
| `null` | Visits evenly split across both |

**Inference rule for natural language → time_bucket:**
- "lunch", "midday" → `afternoon`
- "dinner", "evening", "tonight" → `evening`
- "brunch", "breakfast", "morning" → `morning`
- "late night", "late dinner", "after 10" → `late_night`

---

### Derived Data Layer (for RAG)

**Canonical schema file: `appendix/eval/user_history_schema.md`**

The RAG system aggregates raw booking events into two computed structures. These are rebuilt after every `log_action` call and are what `retrieve_behavioral_context` queries against. They are the stored output of the RAG computation described in Section 7 — not raw user input.

**Restaurant History Record** — one record per unique venue visited, aggregated across all raw events:

```json
{
  "record_id": "string — unique ID, e.g. RH_001",
  "user_id": "string",
  "venue_name": "string — exact name as it appears in the booking system",
  "venue_id": "string | null — OpenTable listing ID if available",
  "location_bucket": "string — neighborhood area (e.g. River North, Riverfront)",
  "cuisine": "string — cuisine type (e.g. Italian, American, Japanese)",
  "typical_time_bucket": "morning | afternoon | evening | late_night — modal time_bucket across visits",
  "typical_day_type": "weekday | weekend | null — null if visits are evenly split",
  "visit_count": "integer — total completed bookings at this venue within window_days",
  "last_visited": "YYYY-MM-DD — date of most recent completed booking",
  "party_size_avg": "float — average party size across visits, rounded to 1 decimal",
  "counterparty_type": "business | personal | null",
  "window_days": 90
}
```

**Ranking rule:** `visit_count` descending → `last_visited` descending (more recent wins on ties).

**`typical_time_bucket`:** The modal time_bucket across all visits to this venue. A venue visited 4 times in the evening and once at lunch has `typical_time_bucket: evening`. Used to filter contextually irrelevant records (a venue the user only visits in the evening should not rank for a lunch query).

---

**Preference Signals** — derived aggregates across all records. Used as the fallback when no venue-level history exists for the queried location or time:

```json
{
  "computed_at": "ISO-8601 timestamp",
  "window_days": 90,
  "cuisines": [
    { "cuisine": "string", "visit_count": "integer", "rank": "integer — 1 = most visited" }
  ],
  "neighborhoods": [
    { "location_bucket": "string", "visit_count": "integer", "rank": "integer" }
  ],
  "time_preferences": [
    { "time_bucket": "morning | afternoon | evening | late_night", "visit_count": "integer", "rank": "integer" }
  ],
  "day_preferences": [
    { "day_type": "weekday | weekend", "visit_count": "integer", "rank": "integer" }
  ]
}
```

**Note:** The eval dataset (`appendix/eval/user_history.json`) uses these derived schemas directly as the seed data for `demo_user_01`. It contains 15 pre-aggregated restaurant history records and computed preference signals.

---

### External APIs
**Primary:** OpenAI GPT-4o (`gpt-4o`) via the OpenAI API — called first for all restaurant searches. Requires `OPENAI_API_KEY` set in `prototype/backend/.env`. Returns real venue names and addresses for any US city or neighborhood.

**Fallback:** Mock dataset — a local static list of real restaurants across Chicago, Los Angeles, New York, San Francisco, Miami, Washington DC, Boston, Seattle, and Austin. Used when OpenAI is unavailable or returns no results.

**Search enrichment:** When the user has no visit history for the requested location and no explicit cuisine preference, the agent infers the user's top cuisine from their preference signals and includes it in the OpenAI query. This ensures the search is personalized even for locations the user has never booked in before.

If both the OpenAI call and the mock fallback return no results, the agent explains in plain language and shows the neighborhoods it has guaranteed mock coverage for.

---

## 7. RAG Strategy

**Trigger:** When a user starts a booking, retrieve past behavior to rank results.

**Process:**
1. Embed the current intent (category + location + time context)
2. Semantically search booking history and chat history for the top 20 nearest records
3. Group by `(category, location, time_bucket)` and compute co-occurrence scores
4. Return patterns with support ≥ 3 and confidence ≥ 0.5 as ranked signals
5. Use these signals to re-rank the options returned by the booking API — do not surface them as explicit suggestions to the user

**Fallback:** If retrieval returns nothing relevant, rank results by rating.

**Preference-signal enrichment for new locations:** When `history_context_applies` is false (no visit history for the queried location and time bucket) and the user has not specified a cuisine, the agent reads `preference_signals.cuisines[0]` and passes the user's top cuisine to the OpenAI search. This means a user who historically prefers Italian will receive Italian suggestions in any new city, not a generic list. The mock fallback is called without this enrichment to preserve its existing filter behavior.

**Freshness:** After every `log_action` call, re-embed the new record and update co-occurrence counts. The output of this aggregation is stored as **Restaurant History Records and Preference Signals** — see Section 6 (Derived Data Layer) for the full schemas, and `appendix/eval/user_history_schema.md` for the canonical schema reference. These are what `retrieve_behavioral_context` queries on every turn.

**Seed data:** Populate the store with 30–60 synthetic restaurant booking events for a demo user, weighted to create at least two replicable behavioral patterns (e.g. user books Italian restaurants on Friday evenings; user consistently chooses quieter spots when party size is 2). Do not seed stated preferences — behavioral inference only.

---

## 8. Privacy Controls

Expose two commands in the system prompt as first-class user rights:

- `show_patterns` — prints all behavioral patterns currently influencing results, so the user can audit what is being inferred
- `forget_me` — deletes the full action-history store for the user and confirms the wipe

---

## 9. Tech Stack

| Layer | Choice |
|---|---|
| Frontend | React chat UI styled to match ChatGPT (web + mobile responsive) |
| Backend | Python (FastAPI, port 8000) |
| Database | SQLite (isolated prototype environment) |
| Vector index | Local (any sentence-embedding model) |

### LLM Roles

| Role | Model | API | When used |
|---|---|---|---|
| Restaurant search | GPT-4o (`gpt-4o`) | OpenAI API | Every search turn — finds real restaurants for any US location, personalized by inferred cuisine from preference signals when no local history exists |
| General chat | GPT-4o (`gpt-4o`) | OpenAI API | Non-booking messages that don't match reservation intent |
| Eval judging | Claude Sonnet 4.6 (`claude-sonnet-4-6`) | Anthropic API | Offline eval runs only — scores D1, D2, D3, D4, D6 per prompt; falls back to string-match if API unavailable |

**Keys required:**
- `OPENAI_API_KEY` — set in `prototype/backend/.env` to enable live restaurant search
- `ANTHROPIC_API_KEY` — set in `prototype/backend/.env` to enable Claude LLM judge in eval runs

---

## 10. Agent Behavior Rules

- **Input validation:** Validate all user inputs before searching. If a field is invalid, retain the valid data and ask only for the invalid field. If partial, store what is given and ask for the rest.
- **Errors:** Never show error codes or technical messages. Explain what happened in plain language and offer one recovery path.
- **No greeting on launch:** The chat interface starts blank. The user initiates the conversation. The agent does not send an opening message.
- **No extra features:** Do not add functionality beyond what is defined in this spec.
- **Consistency:** Write code in a consistent structure and format throughout.
- **No temp fixes:** Address the root cause of bugs, not symptoms.

### Smart Defaults (added 2026-05-17)

The agent minimizes clarifying questions by filling missing parameters from context and history before asking the user:

| Parameter | Default rule |
|---|---|
| `date` | Today — if the user does not specify a date, the agent searches today. No question asked. |
| `time_bucket` | `evening` — if no time keyword is present, evening is assumed. |
| `location` | Top neighborhood from `preference_signals.neighborhoods[0]` — if the user has booking history, the agent uses their most-visited area as the default. If no history exists, the agent asks. |
| `party_size` | Inferred from social context — phrases like "my friend Sarah", "me and John", or "meeting a friend" are interpreted as party of 2. Explicit numeric statements ("party of 4") always take priority. |

**Only `location` is ever asked for.** Date, time, and party size are always resolvable from the message or from defaults. A user with history can say "find me dinner" and receive recommendations immediately with no follow-up questions.

### Intent Inference Rules (added 2026-05-17)

| Pattern | Behavior |
|---|---|
| "I'm meeting my friend / colleague / partner" | Infer party of 2; prime state to receive a neighborhood next |
| "yeah [location]" / "ok [location]" | Strip leading affirmative before parsing location |
| "what about X" / "how about X" | Treat X as a location answer in both CLARIFYING and SELECTING states |
| Party size change only | Reuse the existing recommendation list with an updated header — do not re-run the search |
| "Why did you change the recommendation?" | Explain that a search parameter changed and the list was refreshed; do not return a generic fallback |

### Location Handling (added 2026-05-17)

The agent no longer blocks on unrecognized neighborhoods. Any location is passed through to the search layer. The search order is:

1. **OpenAI** — tried first for all locations. Personalized by inferred cuisine when no local history exists.
2. **Mock data** — fallback if OpenAI is unavailable or returns no results.
3. **"Couldn't find" message** — shown only after both layers return empty. Lists neighborhoods with guaranteed mock coverage and asks the user to pick one.

---

## 11. Deliverables

1. **Runnable entrypoint** — accepts user message via simple HTTP endpoint or stdin; executes the agent loop; returns the assistant's final message plus a JSON log of tool calls
2. **Seed script** — populates the SQLite store with synthetic history in one command
3. **Install + run** — one command to install dependencies, one command to start the demo
4. **Eval script** — replays at least two scripted user turns and asserts: (a) the correct booking tool was called, (b) results were ranked using behavioral context where applicable, (c) no booking was executed without explicit user confirmation, (d) the completed booking was logged to the store

---

## 12. Tool Definitions

All tools referenced in the system prompt. Each must be implemented as a callable function in the backend.

---

### `retrieve_behavioral_context`

Called at step 2 of the agent loop, before searching. Returns ranked history signals used to re-order search results.

**Input:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `user_id` | string | Yes | Authenticated user ID |
| `location` | string | Yes | Neighborhood or area name |
| `date` | YYYY-MM-DD | Yes | Date of the meal |
| `time_bucket` | enum | Yes | `morning` \| `afternoon` \| `evening` \| `late_night` |
| `party_size` | integer | No | Default 1 (agent implementation aligned 2026-05-17) |
| `cuisine` | string \| null | No | Cuisine filter; `null` means no filter |

**Output:**

```json
{
  "history_context_applies": "boolean — true if matching records exist for this query context",
  "restaurant_history": [
    {
      "record_id": "string",
      "venue_name": "string",
      "location_bucket": "string",
      "cuisine": "string",
      "typical_time_bucket": "string",
      "visit_count": "integer",
      "last_visited": "YYYY-MM-DD",
      "party_size_avg": "float"
    }
  ],
  "preference_signals": {
    "cuisines": [{ "cuisine": "string", "visit_count": "integer", "rank": "integer" }],
    "neighborhoods": [{ "location_bucket": "string", "visit_count": "integer", "rank": "integer" }],
    "time_preferences": [{ "time_bucket": "string", "visit_count": "integer", "rank": "integer" }]
  }
}
```

**Retrieval logic:**
1. Filter `restaurant_history` records where `location_bucket` exactly matches `location` AND `typical_time_bucket` matches `time_bucket` AND (cuisine filter matches if provided)
2. If no records survive: set `history_context_applies: false`, return `preference_signals` only
3. Rank surviving records by `visit_count` descending → `last_visited` descending

---

### `search_restaurants`

Called at step 3 of the agent loop. Queries the (mocked) restaurant API and returns available options.

**Input:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `location` | string | Yes | Neighborhood or area name |
| `date` | YYYY-MM-DD | Yes | Date of the meal |
| `time` | HH:MM | Yes | Desired time in 24-hour format |
| `party_size` | integer | Yes | Number of guests |
| `cuisine` | string \| null | No | Cuisine filter |

**Output:**

```json
[
  {
    "venue_id": "string",
    "venue_name": "string",
    "address": "string",
    "cuisine": "string",
    "estimated_cost_per_person": "number",
    "rating": "float",
    "available_times": ["HH:MM"],
    "location_bucket": "string"
  }
]
```

**Ranking:** The agent re-ranks results from this tool using the `restaurant_history` records returned by `retrieve_behavioral_context`. Venues present in history rank above venues not in history, ordered by `visit_count` then `last_visited`. If `history_context_applies: false`, rank by rating.

---

### `book_restaurant`

Called at step 5 of the agent loop, after explicit user confirmation.

**Input:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `user_id` | string | Yes | Authenticated user ID |
| `venue_id` | string | Yes | Venue ID from `search_restaurants` result |
| `venue_name` | string | Yes | Venue name (for logging and confirmation) |
| `date` | YYYY-MM-DD | Yes | Reservation date |
| `time` | HH:MM | Yes | Exact reservation time |
| `party_size` | integer | Yes | Number of guests |
| `counterparty_name` | string | Yes | Name for the reservation |
| `counterparty_phone` | string | Yes | Phone number for the reservation |

**Output:**

```json
{
  "booking_confirmed": "boolean",
  "confirmation_id": "string | null",
  "venue_name": "string",
  "date": "YYYY-MM-DD",
  "time": "HH:MM",
  "party_size": "integer",
  "error_message": "string | null"
}
```

**On failure:** Surface `error_message` in plain language and offer one recovery path (different time, different venue, or link to OpenTable).

---

### `log_action`

Called at step 6 of the agent loop after a successful booking. Writes the raw event to SQLite and triggers re-computation of the derived Restaurant History Record and Preference Signals.

**Input:** Full raw event record (see Section 6 schema). The `outcome` field must be `confirmed`.

**Output:** `{ "logged": boolean, "record_id": string }`

---

### `show_patterns`

Privacy affordance. Returns all behavioral patterns and history records currently influencing results for the authenticated user.

**Input:** `user_id` (string)

**Output:** Full `restaurant_history` array + `preference_signals` for the user.

**Trigger phrases:** "What do you know about me?", "Show my history", "What patterns are you using?"

---

### `forget_me`

Privacy affordance. Permanently deletes all raw events and derived records for the authenticated user.

**Input:** `user_id` (string)

**Output:** `{ "deleted": boolean, "records_removed": integer, "message": string }`

**Trigger phrases:** "Forget everything", "Delete my history", "Stop learning from me"

Confirm user intent before calling. After calling, confirm the deletion in plain language.