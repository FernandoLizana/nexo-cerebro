# P4 — Goal relevance

Implementation: `nexo_qa/goals/relevance.py`.

## Signal

`goal_relevance_score` ∈ [0, 1] — **heuristic proxy**, ENGINEERING DEFAULT, NOT HUMAN-CALIBRATED.

## Inputs

- Token overlap between goal description / entities / active subgoal and target text
- Small synonym expansion (`SYNONYMS` in parser module)
- Entity exact match boost (e.g. `Pro` in action label)
- Domain hints (`find_pricing` boosts plan/price-related labels)

## Outputs

- `goal_relevance_for_text(goal, percept_label)` — for perceptual audit
- `goal_relevance_for_action(goal, action_label, affordance=...)` — for deliberation
- `goal_relevance_map(goal, actions)` — dict `action_id → score`

## Integration path

```text
TaskGoalProcess
  → config["goal_relevance"]
  → PrefrontalDeliberator.run(goal_relevance=...)
       net += 0.22 * relevance
       _pfc_score += 0.35 * relevance
  → EnhancedBasalGangliaProcess
       base_scores += 0.18 * relevance
```

## Separation from P3 signals

| Signal | Layer | Question |
|--------|-------|----------|
| `visibility_score` | P3 perception | Structurally visible? |
| `salience_score` | P3 perception | Heuristic prominence? |
| `goal_relevance_score` | P4 goals | Related to active task? |
| `attention_tier` | P3 gate | Attended this tick? |

**Goal relevance does not override offscreen filtering.** Test: `test_offscreen_still_offscreen_despite_goal`.

## Distractor scenario

Prominent CTA may have high **salience** but low **goal relevance** when goal targets a different label (see `distractor.html` tests).

## Config

No separate YAML in P4 — weights embedded in deliberation blend (0.22 net, 0.35 PFC, 0.18 BG). P9 may externalize calibration.
