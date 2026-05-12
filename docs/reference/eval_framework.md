# Product: ChatGPT Life OS Contextual Action Engine

## Part I: A/B Experiment

### 0.0 Overview

ChatGPT Life OS is a unified consumer surface that lets users move from intent to outcome inside a single conversation across life categories like dining, travel, events, purchases, and scheduling. Today, ChatGPT users complete the thinking part of a task in-app (where to eat, what to do this weekend) and leave to act, breaking continuity and surrendering the high-intent moment to apps like OpenTable, Expedia, and Google. The Contextual Action Engine closes that loop. After a primary action is executed (e.g., booking lunch), the engine inspects the user's action history, identifies a behaviorally grounded pattern (not stated preferences), and surfaces proactive next-best action. For example, "I noticed you usually visit Millennium Park after lunch in this area. Want me to grab park tickets?"

This experiment isolates the chained-suggestion surface and asks one question: does adding a behaviorally inferred chained suggestion after a primary action increase the rate at which users complete multi-step life tasks inside ChatGPT? The unified Life OS shell, the action-history store, and the primary execution tools are held constant in both arms; only the chained suggestion is gated.

### 1.1 Experiment Duration

**TOTAL DURATION:** 60 days for the primary read. This captures 8 full weekly behavioral cycles. Long enough to detect chains that fire on weekly cadences (Friday-night events, weekend trips) without holding back launch. The 28-day monitor reads downstream retention without delaying the launch decision.

### 1.2 What is Changing for the Customer?

**Control (C):** User issues an intent, agent executes the primary action, agent confirms completion, and the turn ends. No proactive suggestion. Identical UI, identical latency profile, identical tool surface.

**Treatment (T1):** Same primary path. After the primary action's confirmation message, if the action-history retrieval surfaces a pattern with support ≥ 3 events and confidence ≥ 0.5 over the last 90 days, the agent appends a proactive suggestion that cites the pattern in plain language ("I noticed you usually …") and offers a one-tap confirmation. If no pattern qualifies, the turn ends silently.

The behavioral inference is default-on for T1 users with a clearly-labeled off-switch in Settings → Personalization → "Let ChatGPT learn from my actions." Keeps the consent narrative defensible without forcing an opt-in modal that would shrink the effective treatment population.

### 1.3 Why is this better for the Customer?

1. Fewer context switches. The user gets the second action proposed in the same surface where the first one happened, rather than re-typing intent in another app.
2. The proposal is grounded in user's behavior, not their stated preferences. It feels like competent assistant who has noticed something rather than a recommender that has been told what to push.
3. Silence is a feature. When no pattern applies, T1 says nothing, so it never becomes a spammer.

The strategic angle for OpenAI is that behavioral action history is the one personalization asset that does not become portable. Anthropic's March 2026 ChatGPT → Claude memory import made stated preferences exportable but observed behavior lives inside the product where it was generated.

### 1.4 What are the key metrics to monitor in this experiment?

**Primary success metric — Weekly multi-step task completion rate:** The percentage of weekly-active users who complete at least one primary action and at least one confirmed chained action within the same calendar week, logged to the action-history store. Expression of the strategy doc's north star (consumers using ChatGPT for end-to-end life workflows, not just answers).

**Guardrail 1 — Opt-out rate from behavioral inference within 14 days:** Direct read on privacy backlash, the top risk flagged in the product strategy. If users feel watched, they will toggle the off-switch, and that is the cleanest leading indicator of negative sentiment we can capture without waiting for support tickets.

**Guardrail 2 — Chained-suggestion rejection rate:** The share of surfaced suggestions the user dismisses or ignores. A high rejection rate means the inference engine is wrong, the surface is intrusive, or both. Either way it indicates the product is degrading trust faster than it is creating value.

**Guardrail 3 — P95 orchestrator-turn latency:** The chained-suggestion path adds a retrieval step, a co-occurrence computation, and one extra tool call. If P95 turn latency regresses past the threshold, the entire orchestrator feels slow, not just the new feature.

### 1.5 How do we expect the key metrics to change?

The primary metric of weekly multi-step task completion rate is expected to increase, with a baseline of approximately 4% (current proxy from Atlas-action telemetry on Plus users) and a hypothesized lift of +2 percentage points absolute (≈50% relative) in T1. The chained suggestion creates the second-action moment that today requires the user to self-initiate. Even modest acceptance on a fraction of eligible turns produces a meaningful lift on a metric that requires the second action to count at all.

Opt-out rate is expected to be low (≤5% within 14 days) because the off-switch is one-tap and the surface stays silent when it has nothing useful to say. Rejection rate is expected to land between 25% and 40%. High enough to be honest about inference imperfection, low enough to validate that the patterns we surface are mostly right. Latency P95 is expected to regress modestly (≤+1sec vs. control) because the retrieval and co-occurrence steps are O(20) records, not full-corpus.

### 1.6 Launch Criteria

**Main objective:** T1 must beat C on weekly multi-step task completion rate by ≥ +1.5 percentage points absolute, statistically significant at α = 0.05 over the 60-day primary read.

**Guardrails (all must hold simultaneously):**
- Opt-out rate within 14 days ≤ 5% in T1
- Chained-suggestion rejection rate ≤ 40% averaged across T1
- P95 orchestrator-turn latency in T1 ≤ control + 1 second

Any guardrail breach blocks launch even if the main metric clears its bar.

### 1.7 Risks and Potential Impact

The chained suggestion may read as surveillance rather than service, particularly on the first eligible turn when the user has not yet built a mental model for why ChatGPT seems to know their habits. If the framing of "I noticed you usually …" lands wrong, it produces both opt-outs and external press risk that is hard to walk back.

A false-positive chained suggestion — one that cites a pattern the user no longer wants to repeat or never owned — damages trust faster than a correct suggestion builds it.

A latency regression beyond the guardrail threshold would degrade the entire orchestrator surface, not just the chained-suggestion turn, because the retrieval call sits inside the main loop.

Finally, the population is bounded to US Plus 25-45 weekly-active, which means a clean read here does not automatically generalize to free-tier users, EU users (where the privacy posture is materially different), or older / less-engaged segments. Launch decisions outside this population will require either replication or argued extrapolation.

---

## Part II: LLM Evaluation Framework

### 0.0 Overview

The Contextual Action Engine is the AI-native MVP at the heart of Life OS. On every turn the orchestrator LLM does four things: parses intent into a tool call, retrieves behavioral patterns from the user's action history, decides whether to surface a chained suggestion grounded in a retrieved pattern, and phrases it citing the pattern faithfully. Because the chained suggestion publicly claims things about the user's own behavior ("I noticed you usually …"), a single fabricated pattern is a legible, personal trust failure of a kind generic LLM mistakes are not. The eval framework is built around that asymmetry.

### 1.1 Eval Set Design (The Golden Dataset)

The golden set contains 300 prompts, stratified across the five Life OS categories (60 prompts per category) and across three provenance buckets:

**Real-user-derived (180 prompts, 60%):** Sampled and anonymized from production Plus-tier traces of users who have completed at least one Life OS turn. Sampling is stratified by category and by whether a behavioral pattern was retrieved for that turn, so the eval reflects the real distribution of pattern-rich and pattern-empty intents.

**Edge cases (90 prompts, 30%):** Hand-authored to exercise the loop's failure modes of missing parameters that force a clarifying question, conflicting patterns (two valid chains with similar confidence), explicit no-pattern cases where the correct behavior is silence, and partially specified intents.

**Adversarial (30 prompts, 10%):** Jailbreak attempts, prompt-injection payloads embedded in venue or counterparty names, attempts to coerce the agent into citing a fabricated pattern, and attempts to extract patterns about other users via crafted user_id-like strings.

Ground truth is hand-labeled by two raters with third-rater tiebreak. Each label captures: expected primary tool call and parameters, the specific pattern_id to cite if a chain is correct, a `silence_expected` flag, and a `must_refuse` flag for adversarial prompts. The set is versioned in source control alongside the agent prompts, so any regression is bisectable to a specific change.

### 1.2 Technical Performance Metrics

**Hallucination rate:** Share of chained suggestions whose cited pattern cannot be traced to a record returned by `retrieve_behavioral_context` on that turn. Detection is automated. A runtime checker string-matches the cited pattern fingerprint against the retrieved set. Target 0% tolerance, because each fabrication is observable to the user and damages trust faster than a correct suggestion.

**Correctness:** Composite of 4 binary subscores. Primary tool selected correct, parameters extracted correct, chain-vs-silence decision correct, suggestion phrasing faithful to the cited pattern. A turn passes only if all four are 1.

**Latency:** End-to-end orchestrator turn (user input → final message), with P50 ≤ 2.0s, P95 ≤ 4.0s. P95 is load-bearing because the chained path adds a retrieval and a co-occurrence step.

**Cost:** Target $0.012 per turn, derived from Plus ARPU and the Life OS gross-margin floor.

### 1.3 Business KPI Alignment

The eval metrics are deliberately one-to-one with the Part I A/B guardrails. Pattern-fabrication rate maps to opt-out rate as each fabrication is a leading indicator of a privacy-driven opt-out. Composite accuracy maps to weekly multi-step task completion rate as a wrong tool call or wrong chain breaks the multi-step path and the user reverts to OpenTable, Google, or Expedia. Latency P95 maps to active retention as internal Atlas-action telemetry shows +1s on action turns reduces D7 retention by ~3%. Cost per turn maps to Plus gross margin via the unit economics above. A green eval run is therefore a precondition for the A/B launch decision, not a parallel exercise.

### 1.4 Evaluation Strategy: Human-in-the-Loop vs. Agent-as-a-Judge

The strategy is hybrid: GPT-4o as primary judge grades all 300 prompts on every weekly regression run, and a stratified 10% human audit (30 prompts, weighted toward edge and adversarial slices) is performed by the PM plus one trained rater. The judge sees the prompt, the agent's full trace (retrieval results, tool calls, final message), and the ground truth, and outputs pass/fail per dimension with a rationale.

Justification: 300 prompts × four dimensions × weekly cadence = 1,200 ratings/week. Pure-human grading doesn't scale to that cadence; pure LLM-judge is unsafe on the dimensions where LLM graders are systematically weak — tone and creepiness of the chained suggestion, edge-case judgment, subtle pattern misattribution. The human audit targets those dimensions. We track judge-vs-human agreement per dimension; if any drops below 85%, that dimension is made human-only until judge prompt is fixed.

### 1.5 Success and Guardrail Metrics

**Main objective:** Composite accuracy ≥ 90% on the full 300-prompt golden set.

**Guardrails (all must hold simultaneously for launch):**
- Pattern-fabrication rate = 0% on all 300 prompts
- 100% refusal rate on the `must_refuse` adversarial slice
- Orchestrator-turn P95 latency ≤ 4.0 seconds
- Cost per turn ≤ $0.012

The fabrication and adversarial-refusal bars are zero-tolerance. A single failure blocks launch because both correspond to legible, personal failure modes that cannot be made up for by correct ones.

### 1.6 Reliability and Safety Guardrails

A pattern-grounding validator runs after every chained suggestion is generated and before it reaches the user, re-checking that the cited pattern exists in the retrieval result. On mismatch, the suggestion is suppressed and an internal alert fires. This is the single most important safety control because it catches fabrications even when the eval misses them. PII redaction runs on the log-write path only, so counterparty names remain usable for the current turn but never reach the action-history store in raw form. A jailbreak classifier on user input short-circuits the orchestrator before any tool call. Rate-limiting on `retrieve_behavioral_context` blocks high-volume probing. The user-facing `show_patterns` and `forget_me` tools are first-class and the public answer to the privacy-backlash narrative.

### 1.7 Risks and Potential Impact

**Model drift:** GPT-5 improves or regresses silently, shifting pass rates without code changes. Mitigation: pin the model version in every eval run, alert on week-over-week subscore deltas, and refresh the real-user slice quarterly while freezing edge and adversarial slices for longitudinal comparability.

**Cost overruns:** The chained-suggestion path adds tokens to roughly half of all turns. Mitigation: hard token cap on the suggestion, per-turn cost monitoring with a $0.014 alert threshold.

**Judge-LLM blind spots on creepiness:** GPT-4o is systematically more permissive than humans on surveillance suggestions, even when grounded in a real pattern. Mitigation: human audit is weighted toward this dimension and the shipping bar on "creepiness" stays conservative even when the judge passes it.
