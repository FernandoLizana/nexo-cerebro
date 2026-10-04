# P1 — Legacy compatibility

v90 continues to run unchanged for the golden scenario.

## Before P1

- PFC filtered candidates through `ROOM_ACTION_SCHEMAS` living in `nexo/prefrontal/deliberation.py`.
- `DriveField.action_bias` used a name table (`eat` → hunger, …).
- Motor called `world.apply_action` and emitted `reward.received` with `{value}`.
- v90 facade lacked `available_actions`; scheduler swallowed AttributeError; legacy adapter produced 12× explore.

## After P1

- Same verbs, same effects, same configs (`configs/nexo/integrated_v90.yaml` untouched).
- Catalog lives in `nexo/core/legacy_action_adapter.py`.
- `from nexo.prefrontal.deliberation import ROOM_ACTION_SCHEMAS` still works.
- `action_bias("eat")` equals `schema_bias(schema_from_legacy_action("eat"))`.
- Motor still calls `apply_action`; extra outcome fields on `reward.received` do not enter `trajectory_hash`.
- `action.selected` may include `candidate_action_ids`; hash still uses `{tick, type, action}` only.

## Mapping

| Legacy id | affordance | action_type | target |
|-----------|------------|-------------|--------|
| eat | consumable | consume | food_source |
| rest | restorable | recover | self |
| flee | avoidable | avoid | safe_zone |
| approach_caregiver | approachable | social | caregiver |
| explore | navigable | explore | environment |
| inspect_distractor | inspectable | inspect | distractor |

Execution mapping: `ActionSchema.id` → same string → `world.apply_action(id)`.

## Tests

- `tests/test_executive_integrated.py::test_pfc_veto_inhibits_distractor_when_low_energy`
- `tests/test_p1_environment_contract.py` adapter round-trip
- v90 golden hash (STRICT)

## Behavioral baseline

```text
trajectory_hash = 77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c
actions_taken   = 12 × explore
final_energy    = 0.3526710863756767
mean_reward     = 0.12
valid_certificates = 12
agency_score    = 1.0
event_count     = 421
```

## Known differences

**None on the STRICT golden.** Informational: `reward.received` payload has extra keys; `action.selected` has extra keys. Event **count** unchanged.

Gate no-go fallback: if `"rest"` is not in candidates, use the first candidate. RoomWorld always lists `rest`, so v90/RoomWorld behavior is unchanged.
