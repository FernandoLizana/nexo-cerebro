# P1 — Environment contract

## Interface (exact)

`nexo/core/environment_protocol.py` · `EnvironmentProtocol`

| Method | Input | Output |
|--------|-------|--------|
| `percepts_for_agent` | none | `list[tuple[str, float, tuple[float, ...]]]` modality, salience, embedding |
| `available_actions` | none | `tuple[str, ...]` stable string ids for this decision cycle |
| `action_info` | `action: str` | `base_value`, `cost_energy`, `risk`, `modality` |
| `apply_action` | `action: str` | `reward`, `homeostatic_deltas`, `encoded_memory`, optional `accepted`/`error` |
| `sync_from_body` | body | optional; copies energy into some worlds |
| `action_schemas` | none | optional `tuple[ActionSchema, ...]` |

Helpers:

- `action_schemas_for(world)` — no `isinstance` on RoomWorld/MockWorld.
- `apply_action_outcome(world, action_id)` — wraps apply as `ActionOutcome` without changing the raw dict used by reward.

## Responsibilities

**Environment**

- What can be perceived.
- Which actions exist **now**.
- What each action means (schema / `action_info`).
- Execute the chosen id and return consequences.

**Cognitive core**

- Score candidates.
- Select one id.
- Learn from `reward.received` / homeostatic events.
- Must not branch on world class or browser payloads.

## Lifecycle (real scheduler order)

```text
Agent
 │
 │ percepts_for_agent
 ▼
Environment
 │
 │ percepts
 ▼
Cognition (PFC)
 │
 │ available_actions + ActionSchema[]
 ▼
ActionGate / basal ganglia
 │
 │ action.selected  (id + candidate_action_ids)
 ▼
MotorExecutionProcess
 │
 │ apply_action → ActionOutcome
 ▼
reward.received / homeostasis / memory / causal.certificate
```

`transition_id` is the existing event `tick` (not a parallel id system).

## Errors

| Kind | Representation |
|------|----------------|
| Domain: action unavailable / rejected | `ActionOutcome.accepted=False`, `error` string; still emits `reward.received` |
| Programming: empty id, NaN risk, duplicate ids | `ActionSchemaError` (fail hard) |
| Missing `available_actions` on a world | `AttributeError` swallowed by `CognitiveScheduler` (preexisting; v90 facade) |

## Side effects

`apply_action` mutates world state. Motor also applies `MetabolismEngine.apply_action` when a homeostatic controller is present (unchanged physiology path).

## Examples

**Legacy:** `RoomWorld.available_actions()` may include `eat` only while `food_available`.

**MockWorld:** `closed → inspect_panel|wait`; `armed → activate_switch|step_back`; `open → collect_target|step_back`; `done → finish`.

## v90 exception

`WorldDemoFacade` implements percepts/`action_info`/`apply_action` but **not** `available_actions`. Integrated PFC/BG throw; the early legacy adapter still selects the mapped explore/wander path. **Do not “fix” this in P1** — it is the golden trajectory.
