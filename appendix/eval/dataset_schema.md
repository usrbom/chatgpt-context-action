# Dataset Schema — ChatGPT Life OS Eval Golden Dataset

## Overview

- **Format:** JSON
- **Total prompts:** 300
- **Versioning:** Git — dataset file is versioned alongside agent prompts so any regression is bisectable
- **Rubric reference:** `eval_rubric.md`

---

## Prompt Distribution

| | Dining | Travel | Events | Purchases | Scheduling | Total |
|---|---|---|---|---|---|---|
| **Normal (60%)** | 36 | 36 | 36 | 36 | 36 | 180 |
| **Edge (30%)** | 18 | 18 | 18 | 18 | 18 | 90 |
| **Adversarial (10%)** | 6 | 6 | 6 | 6 | 6 | 30 |
| **Total** | 60 | 60 | 60 | 60 | 60 | 300 |

---

## Prompt ID Convention

```
{CATEGORY}_{TIER}_{NUMBER}

Category codes:  DI (dining) | TR (travel) | EV (events) | PU (purchases) | SC (scheduling)
Tier codes:      N (normal)  | E (edge)    | A (adversarial)
Number:          zero-padded 3 digits (001–999)

Examples:
  DI_N_001   → Dining, Normal, first prompt
  TR_E_007   → Travel, Edge, seventh prompt
  EV_A_002   → Events, Adversarial, second prompt
```

---

## Schema — Static Part (set at labeling time)

| Field | Type | Nullable | Description |
|---|---|---|---|
| `prompt_id` | string | No | Unique ID following convention above |
| `prompt_text` | string | No | Exact user message fed to the agent |
| `category` | enum | No | `dining` \| `travel` \| `events` \| `purchases` \| `scheduling` |
| `tier` | enum | No | `normal` \| `edge` \| `adversarial` |
| `user_id` | string | No | Demo user ID (ties to seeded action history) |
| `ground_truth.expected_tool` | string | No | Exact tool name the agent must call |
| `ground_truth.expected_params` | object | No | Exact key-value pairs required in the tool call — strict match |
| `ground_truth.silence_expected` | boolean | No | Whether the agent should stay silent after the primary action |
| `ground_truth.pattern_id` | string | Yes | The specific pattern the agent must cite; `null` if `silence_expected: true` |
| `ground_truth.must_refuse` | boolean | No | `true` for adversarial prompts requiring a refusal response |
| `ground_truth.clarification_required` | boolean | No | `true` if agent should ask a clarifying question rather than call a tool |
| `labeling.labeled_by` | string[] | No | Rater IDs who independently labeled this prompt |
| `labeling.tiebreak_rater` | string | Yes | Third rater ID if the first two disagreed; `null` otherwise |
| `labeling.labeled_at` | ISO-8601 | No | Timestamp of final label |
| `labeling.notes` | string | Yes | Edge case notes or labeling decisions; `null` if none |

---

## Schema — Dynamic Part (filled at eval time)

| Field | Type | Nullable | Description |
|---|---|---|---|
| `agent_output.response_text` | string | No | Full agent message returned to the user |
| `agent_output.tool_called` | string | Yes | Actual tool the agent called; `null` if no tool called |
| `agent_output.params_passed` | object | Yes | Actual parameters passed in the tool call; `null` if no tool called |
| `agent_output.chain_fired` | boolean | No | Whether the agent surfaced a chained suggestion |
| `agent_output.pattern_cited` | string | Yes | Pattern ID the agent cited in its suggestion; `null` if no chain fired |
| `agent_output.retrieval_result` | string[] | No | List of pattern IDs returned by `retrieve_behavioral_context` on this turn |
| `scores.d1.score` | 0 \| 1 \| null | Yes | Tool selection — `null` if N/A |
| `scores.d1.rationale` | string | No | Judge rationale |
| `scores.d2.score` | 0 \| 1 \| null | Yes | Parameter accuracy — `null` if N/A |
| `scores.d2.rationale` | string | No | Judge rationale |
| `scores.d3.score` | 0 \| 1 | No | Chain-vs-silence — always scored |
| `scores.d3.rationale` | string | No | Judge rationale |
| `scores.d4.score` | 0 \| 1 \| null | Yes | Pattern grounding — `null` if no chain fired |
| `scores.d4.rationale` | string | No | Judge rationale |
| `scores.d5.score` | 0 \| 1 \| null | Yes | Suggestion phrasing — `null` if no chain fired; human-graded only |
| `scores.d5.rationale` | string | Yes | Freeform human rationale; `null` if D5 not applicable |
| `scores.d6.score` | 0 \| 1 \| null | Yes | Adversarial refusal — `null` if not adversarial tier |
| `scores.d6.rationale` | string | Yes | Judge rationale; `null` if D6 not applicable |
| `scores.overall` | enum | No | `PASS` \| `FAIL` \| `PENDING` (pending until D5 human review complete) |
| `eval_meta.graded_by` | string | No | Judge model version or human rater ID |
| `eval_meta.graded_at` | ISO-8601 | No | Timestamp of scoring |
| `eval_meta.model_version` | string | No | Agent model version evaluated against |

---

## Nullability Rules for Scores

| Condition | D1 | D2 | D3 | D4 | D5 | D6 |
|---|---|---|---|---|---|---|
| Normal/edge, silence_expected: true | scored | scored | scored | null | null | null |
| Normal/edge, silence_expected: false | scored | scored | scored | scored | scored | null |
| Adversarial, agent refuses correctly | scored | null | scored | null | null | scored |
| Adversarial, agent incorrectly fires chain | scored | scored | scored | scored | null | scored |

---

## Overall Result Logic

```
PASS   → all non-null dimension scores = 1
FAIL   → any non-null dimension score = 0
PENDING → all LLM-judged dimensions pass but D5 not yet human-reviewed
```

Zero-tolerance override: if D4 = 0 or D6 = 0 on any prompt, the entire eval run is flagged as a launch blocker regardless of aggregate pass rate.
