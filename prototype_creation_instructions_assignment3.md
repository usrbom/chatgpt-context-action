## 1. Overview
### 1.1 Problem
ChatGPT's 900M weekly users treat it as an answer engine, then leave the app to
act. They ask ChatGPT where to eat, then open apps like OpenTable. They plan a
trip, then switch to Expedia. Every context switch breaks continuity, drops the
behavioral signal and hands the high-intent moment to a competitor. The memory of
*stated* preferences is now portable (Anthropic's ChatGPT→Claude import, March
2026), so the moat has shifted to what a user has actually *done* inside the
product, preferences that compounds silently and cannot be exported.
The core product gap: ChatGPT has no unified execution layer that observes real
behavior across task types, infers patterns from that behavior and proactively
chains next-best actions inside a single interface.
### 1.2 Goals
The prototype must demonstrate three capabilities in one agent loop:
1. **Unified intent handling.** A user can issue a natural-language request across
any of five life categories like dining, travel, events, purchases, scheduling and
the agent routes, plans and executes without the user leaving the interface.
2. **Behavioral inference.** The agent reads an action-history store, detects a
repeating pattern relevant to the current intent, and surfaces a proactive chained
suggestion (not from stated preferences but from observed behavior).
3. **One-tap execution with logging.** Confirmed actions are written back to the
action-history store, strengthening the pattern for next time.
### 1.3 Scope
**In scope for the prototype**
The agent handles one orchestrator turn end-to-end: parse intent, retrieve relevant
behavioral patterns, call the appropriate execution tool (dining, travel, events,
purchases, scheduling), generate a chained suggestion grounded in action history,
and log the outcome. The action-history store is a local file (JSON or SQLite)
seeded with 30-60 synthetic events spanning all five categories. A minimal CLI or
web interface is sufficient; visual polish is not required.
**Out of scope**
No Atlas browser embedding, no real payment rails, no Codex or coding tool surface.
Real third-party APIs (OpenTable, Ticketmaster, etc.) to be called behind a uniform
tool interface so the agent loop is testable without credentials.
### 1.4 Target User & Success Metric
The primary user is an urban professional aged 25–45, non-technical, already a
daily ChatGPT user. The single success metric for the prototype: the agent
completes ≥1 multi-step task (primary action + at least one behaviorally-inferred
chained action) in a single conversation, with both actions logged back to the
history store. If the chained suggestion is not behaviorally grounded (i.e., cannot
be traced to a pattern in the seeded history), the prototype fails the test.
## 2. Agent System Prompts
```
You are ChatGPT Life OS, a consumer life operator. Your job is to move a user
from intent to outcome in a single conversation, across five categories:
dining, travel, events, purchases, scheduling.
On every user turn, follow this loop:
1. INTENT. Identify the primary category and the concrete parameters needed

to execute (who, what, when, where). If a required parameter is missing
and cannot be safely inferred, ask 1 clarifying questions max.
2. BEHAVIORAL CONTEXT. Before you act, call retrieve_behavioral_context with
the user's id, the parsed intent, and location if known. Read the returned
patterns as FACTS about past behavior, not preferences the user stated.
3. PRIMARY EXECUTION. Call the single booking/purchase/scheduling tool that
fulfills the stated intent. Do not batch unrelated actions here.
4. CHAINED INFERENCE. Inspect the retrieved patterns. If and only if a
pattern is triggered by the current action (e.g., "after lunch near
Riverfront, this user has booked park tickets 4 of the last 5 times"),
propose ONE chained action using ask_user_confirmation. Your proposal
MUST cite the pattern in plain language ("I noticed you usually ...").
Never propose a chained action that cannot be grounded in a retrieved
pattern. Silence is correct when no pattern applies.
5. LOG. After each successful tool call, call log_action with the full
payload and outcome. Logged events feed the next turn's retrieval.
Rules that override everything else:
- Never execute a chained action without an explicit user confirmation turn.
- Never fabricate a behavioral pattern. If retrieve_behavioral_context
returns nothing relevant, skip step 4 entirely.
- Treat location, time, and social context as sensitive. Do not echo them
back to the user unless they are load-bearing for the current decision.
- Prefer one action per turn plus at most one chained proposal. Resist the
urge to stack suggestions; the user can always ask for more.
- If a tool fails, surface the failure plainly and offer one recovery path.
Your tone is that of a calm, competent chief of staff: concise, proactive
where grounded, and quiet where not.
```
## 3. Context
### 3.1 Data Requirements
The prototype needs one seeded dataset: **action history**. Each record is a single
completed action by the user, written at the moment of completion. The minimum
schema:
```
{
"event_id": "uuid",
"user_id": "string",
"timestamp": "ISO-8601",
"category": "dining | travel | events | purchases | scheduling",
"action": "string (e.g., 'book_dining', 'complete_purchase')",
"payload": {
"title": "string",
"location": { "name": "string", "lat": "number", "lon": "number" },
"time": "ISO-8601",
"counterparty": "string? (restaurant, vendor, attendee)",
"amount": "number?",
"category_tags": ["string"]
},
"outcome": "confirmed | failed | cancelled",

"session_id": "string (groups actions taken in one conversation)"
}
```
Initiate the store with 30-60 synthetic events for a single demo user, weighted to
create at least two *replicable* behavioral patterns. for example, (a) lunch near
Riverfront followed by a Millennium Park ticket purchase on 4 of 5 occasions, and
(b) Friday evening event bookings followed by a rideshare scheduled 30 minutes
after end time. Patterns must be dense enough.
Do not seed stated preferences (favorite cuisines, dietary restrictions). The
differentiator is behavioral inference; stated preferences would muddy the eval.
### 3.2 RAG Strategy
Retrieval is behavioral-pattern retrieval, not document retrieval.
**Stage 1 - semantic recall.** Embed each action record's concatenated `category +
payload.title + payload.location.name + category_tags` using any sentence-embedding
model. Store in a local vector index. On retrieval, embed the current intent string
plus any location/time context and pull the top 20 nearest records.
**Stage 2 - pattern synthesis.** Over the 20 recalled records, group by `(category, location_bucket, time_bucket, counterparty_type)` and compute a simple co-occurrence score: for each pair of categories that appear in the same `session_id` or within a 3-hour window, count occurrences over the last 90 days and divide by the count of the antecedent alone. Return any pair with support ≥ 3 and confidence ≥ 0.5 as a "pattern" with a plain-English template:
After {antecedent_action} near {location}, this user has {consequent_action} {confidence*100}% of the time over the last 90 days."
The orchestrator consumes these templates directly; the LLM does not re-infer the pattern from raw records. This keeps behavioral claims auditable as every surfaced suggestion points back to a computed statistic, not a hallucinated one.

**Freshness.** After every `log_action` call, re-embed the new record and incrementally update the co-occurrence counts. The prototype does not need real-time streaming; a synchronous update at the end of each turn is sufficient.

What RAG is NOT used for : General world knowledge (restaurant menus, event
listings, flight prices) must come from the stubbed tools, not the vector store.
The store is exclusively the user's own action history.
## 4. Privacy & Consent (required for the prototype)
The agent must surface two affordances even in the prototype:
1. a command that prints the full pattern list currently influencing its
suggestions so the user can audit what is being inferred about them;
2. a command that deletes the action-history store for a given user_id and confirms
the wipe. These are two extra tools: `show_patterns(user_id)` and
`forget_me(user_id)` and they belong in the system prompt as first-class rights,
not buried features. This is to mitigate privacy-backlash risk called out in the
product strategy.
## 5. Build Instructions for Claude Code
Claude Code should build the project in whatever language and libraries it judges
best-fit and the stack is intentionally left open. Required deliverables:

A runnable entrypoint that accepts a user message on stdin or a simple HTTP
endpoint, executes the orchestrator loop and prints the assistant's final message
plus a JSON log of tool calls. A seed script that populates the action-history
store with the two planted patterns with one command to install dependencies and
one command to run the demo. An eval script that replays three scripted user turns
("Book me lunch with Sarah on Friday near Riverfront", "Plan a weekend trip to
Austin", "Remind me to pick up a gift before Thursday") and asserts, for each, that
(a) the primary tool was called, (b) at least one behaviorally-grounded chained
suggestion was surfaced when a pattern applied, and (c) both actions were logged on
confirmation.