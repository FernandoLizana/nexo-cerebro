# P1 — ActionSchema

Module: `nexo/core/action_schema.py`

Frozen dataclass (`slots=True`). `metadata` is wrapped in `MappingProxyType`.

## Fields

| Field | Required | Range / rule | Semantics |
|-------|----------|--------------|-----------|
| `id` | yes | non-empty string | Identity for this decision cycle. Never `id(obj)`. |
| `label` | yes | non-empty string | Human-readable. |
| `action_type` | no | generic label (`consume`, `inspect`, `activate`, …) | Not a browser opcode. |
| `target` | no | conceptual (`food_source`, `panel`, …) | Not a locator. |
| `affordance` | no | e.g. consumable/inspectable/selectable | Cognitive category. |
| `expected_effect` | no | predicted drive/effect label | Not the real reward. |
| `estimated_cost` | no | finite float or None | Mapped from `action_info.cost_energy`. |
| `risk` | no | finite, in `[0, 1]` if set | Mapped from `action_info.risk`. |
| `metadata` | no | JSON-safe mapping | Opaque to PFC. |

## Identity

Stable for the cycle that listed the catalog. RoomWorld keeps the legacy verb as `id` so execution is reversible. MockWorld uses its own verbs (`inspect_panel`, …).

## Serialization

`to_dict` / `from_dict` are JSON-safe. No handles, lambdas, or process refs.

## Lifecycle

Environment lists actions → `action_schemas_for` → PFC/BG score → `action.selected` stores `selected_action_id` + `candidate_action_ids` → motor applies `id` → `ActionOutcome`.

## What it must not contain (cognitive dependency)

```text
FORBIDDEN AS COGNITIVE DEPENDENCY:
CSS selectors
XPath
driver references
DOM handles
RoomWorld pointers
Python object ids
```

`metadata` may hold environment keys for logging, but `_pfc_score` does not read them (see `test_pfc_does_not_require_room_names_or_metadata_keys`).

## ActionOutcome

`accepted`, `success`, `reward`, `observations`, `error`, `metadata`. Domain rejection is data, not an exception. Invalid schemas are `ActionSchemaError`.
