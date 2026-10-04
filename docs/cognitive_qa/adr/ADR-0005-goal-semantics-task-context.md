# ADR-0005 — Goal semantics and task context (P4)

## Status

Accepted — P4 (2026-08-19)

## Context

P3 delivered perceptual scenes but NEXO could not use declarative NL goals to steer web tasks (`P2_LIMITATION_GOAL_SEMANTICS`). P4 must wire goals without step scripts or oracle leakage.

## Decision

1. Add `nexo_qa/goals/` with `Goal`, `TaskContext`, `GoalProgress`, limited NL parser, relevance, progress evaluation.
2. `TaskGoalProcess` emits `goals.updated`, `goal.progress`, `goal.relevance` into the existing event pipeline.
3. `bind_task()` registers the process and sets scheduler config — no `BrowserWorld` import in `nexo` core.
4. Minimal PFC/BG changes: optional `goal_relevance` dict boosts deliberation scores.
5. Oracle predicates live in `nexo_qa/scenarios/oracle.py` — tests only.

## Consequences

- Goals are declarative, serializable, step-free.
- Task context provides agent-visible data only.
- v90 golden unchanged; legacy worlds unaffected without `bind_task`.
- No LLM required; synonym/token heuristics only.

## Alternatives rejected

- Hardcoded REGISTER_PRO step tables in runtime.
- Importing oracle into deliberation.
- Replacing NEXO goal stack entirely for homeostatic tasks.
