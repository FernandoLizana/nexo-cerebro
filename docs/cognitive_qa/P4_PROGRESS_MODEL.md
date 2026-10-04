# P4 — Progress model

Implementation: `nexo_qa/goals/progress.py` — `evaluate_progress()`.

## Principle: evidence, not steps

Progress is **ordinal**, derived from:

- Current URL path and query params
- Action history labels (observed, not prescribed)
- Constraint satisfaction
- Policy block signals

Progress is **never** computed as `step_index / total_steps`.

## Progress levels

| Level | Meaning |
|-------|---------|
| `unknown` | Insufficient evidence |
| `none` | No observable advancement |
| `partial` | Flow started or mid-form |
| `high` | Near completion (e.g. on `plan.html` with Pro selected in history) |
| `complete` | Success URL + matching plan constraint |
| `blocked` | Policy or hard block |

## Goal status coupling

| Observation | Typical status |
|-------------|----------------|
| `index.html`, no actions | `none` / ACTIVE |
| `name.html` | PARTIALLY_SATISFIED |
| `plan.html` + Pro in history | PARTIALLY_SATISFIED → high |
| `success.html?plan=pro` | SATISFIED |
| `POLICY_BLOCKED` | BLOCKED |

## Non-monotonic progress

Changing from Pro to Basic on `plan.html` re-evaluates progress — may drop from `high` to `partial`. No automatic rollback script; evidence-driven only.

## Evidence field

Each `GoalProgress` carries `evidence: tuple[str, ...]` e.g.:

```text
url:plan
url:success plan=pro
form_started
```

For causal audit — see `goal.progress` events in trace.

## Events

`TaskGoalProcess` emits:

```text
goal.progress  { goal_id, progress, active_subgoal }
```

## Anti-cheat invariant

Tests verify progress does not reference oracle step lists. Oracle knows `success.html?plan=pro`; runtime progress inferrs the same from **observed URL**, not from hidden step counter.
