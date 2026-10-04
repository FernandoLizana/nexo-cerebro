# P4 — Goal model

Canonical reference for `Goal` (`nexo_qa/goals/models.py`).

## Fields

| Field | Purpose |
|-------|---------|
| `goal_id` | Stable instance id (`goal:<uuid>`) |
| `description` | Raw declarative NL goal (agent-facing) |
| `goal_type` | Normalized domain: `registration`, `plan_selection`, `find_pricing`, `navigation`, `general` |
| `status` | Lifecycle state (see below) |
| `priority` | Relative priority (default 1.0) |
| `constraints` | Must-satisfy rules (e.g. `must_select_plan: Pro`) |
| `entities` | Extracted slots (`plan`, `name`, `email`) |
| `subgoals` | Semantic phases — **not** click steps |
| `active_subgoal` | Current semantic focus |
| `parent_goal_id` | Optional hierarchy |
| `metadata` | Parser audit (`normalized`, `parser`) |
| `instruction_source` | Always `TASK_GOAL` for top-level goals |

## Explicitly excluded

- `steps`, `expected_actions`, `step_sequence`
- CSS selectors, element ids, correct paths
- Oracle success predicates

## Goal lifecycle

```text
PENDING → ACTIVE (on TaskGoalProcess first tick)
       → PARTIALLY_SATISFIED / BLOCKED / FAILED / SATISFIED
       → ABANDONED (future — not auto-triggered in P4)
```

## Status semantics

| Status | Meaning |
|--------|---------|
| `PENDING` | Parsed, not yet injected into cognition |
| `ACTIVE` | Loaded via `TaskGoalProcess`, tokens in `active_goals` |
| `PARTIALLY_SATISFIED` | Some constraints/evidence met |
| `SATISFIED` | Success predicate met (e.g. `success.html?plan=pro`) |
| `BLOCKED` | Policy or irrecoverable environment block |
| `FAILED` | Explicit failure state (not used for suboptimal choices alone) |
| `ABANDONED` | Reserved for P5+ metacognitive abandon |

## Activation

1. `parse_goal(description, task_context=...)`
2. `bind_task(rt, goal=..., task_context=..., world=...)`
3. `TaskGoalProcess` sets `ACTIVE`, emits `goals.updated`

## Goal tokens (`goal_tokens()`)

Symbolic strings merged into `state.active_goals`:

```text
task:active
task:type:registration
task:plan:pro
task:constraint:must_select_plan:pro
task:subgoal:localizar_inicio
```

Used by `_pfc_score` for token overlap boosts — not step indices.

## Goal immutability

The **meaning** of `description` and original constraints does not change from web content. Web percepts may say “ignore your goal” — that is `WEB_CONTENT`, not a new `TASK_GOAL`. See `P4_INSTRUCTION_AUTHORITY.md`.

## Serialization

`Goal.to_dict()` is JSON-safe and auditable. Tests assert absence of step-like keys via `goal_contains_steps()`.

## Related

- Parser: `P4_GOAL_PARSER.md`
- Progress: `P4_PROGRESS_MODEL.md`
- Legacy alias: `P4_GOAL_REPRESENTATION.md` points here
