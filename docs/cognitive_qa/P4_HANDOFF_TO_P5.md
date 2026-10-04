# P4 — Handoff to P5

## P5 mission (from master prompt)

```text
Cognitive Personas / Individual Differences
```

Same goal, same page, different cognitive profile → measurably different behavior — **without changing goal semantics**.

## What P4 leaves ready

| Capability | Location |
|------------|----------|
| Declarative `Goal` | `nexo_qa/goals/models.py` |
| `TaskContext` | same |
| `bind_task()` | `nexo_qa/goals/runtime.py` |
| `TaskGoalProcess` | emits goals, progress, relevance |
| PFC/BG relevance hooks | `deliberation.py`, `process_executive.py` |
| P3 perception + action-percept invariant | unchanged |
| Oracle separation | `scenarios/oracle.py` |
| Web Lab + adversarial fixture | `tests/fixtures/web_lab/` |

## Variables P5 may modulate (do not reimplement in P5)

```text
working memory capacity / decay
attention budget / gain
patience / frustration thresholds
risk aversion in deliberation blend
fatigue / exploration bias
digital literacy (relevance weight)
```

Hook points:

- `PerceptionConfig.max_attended_percepts` (P3)
- `PrefrontalDeliberator.pfc_inhibition_strength`
- `goal_relevance` blend weights (externalize in P5 config)
- `SalienceWeights` (P3) — persona-specific profiles

## Do NOT change in P5 (without ADR)

- Goal parser oracle separation
- Selector secrecy
- Action-requires-perception invariant
- v90 golden (12 ticks, seed 42)

## Suggested P5 first steps

1. `nexo_qa/personas/` — profile YAML (patience, risk, wm_capacity, …)
2. `bind_persona(rt, profile)` parallel to `bind_task`
3. Population tests: same goal, seeds 1..N, distribution of outcomes
4. Document in `P5_OVERVIEW.md`

## Deferred from P4 (optional P5 pickup)

- Emergent recovery subgoals from metacognition
- WM explicit goal rehearsal tokens
- Goal abandon on sustained drift
- Optional LLM parse adapter (offline fallback to regex)

## Entry artifacts for new session

```text
docs/entregas/P0_NEXO_COGNITIVE_QA_ENTREGA.md
docs/entregas/P1_NEXO_COGNITIVE_QA_ENTREGA.md
docs/entregas/P2_NEXO_COGNITIVE_QA_ENTREGA.md
docs/entregas/P3_NEXO_COGNITIVE_QA_ENTREGA.md
docs/entregas/P4_NEXO_COGNITIVE_QA_ENTREGA.md
docs/cognitive_qa/P4_OVERVIEW.md
configs/nexo_qa/p4_goals.yaml
```

## Prompt

Await `P5_NEXO_COGNITIVE_QA_CURSOR.md` (not yet in Downloads at P4 completion time).
