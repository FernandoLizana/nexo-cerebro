# P1 — Environment contract review (P0 vs code)

P0 document `P0_CURRENT_ENVIRONMENT_CONTRACT.md` remains accurate. Differences after P1 are **additive**.

## Confirmed in code

| Question | Answer |
|----------|--------|
| What class is the environment? | Duck-typed `runtime.world` from `create_world`. Default tests: `RoomWorld`. v90: `WorldDemoFacade`. |
| Who perceives? | `RawSensoryCaptureProcess` / `SensoryRelayProcess` → `percepts_for_agent`. |
| Who lists actions? | PFC + BG → `available_actions`. |
| Who values them? | `action_info` + `DriveField.schema_bias` + PFC `_pfc_score` on `ActionSchema`. |
| Who selects? | `ActionGate.select` → `action.selected`. |
| Who executes? | `MotorExecutionProcess` → `apply_action` (now via `apply_action_outcome`). |
| Reward path | `reward.received` `payload.value` (plus optional `action_id`/`accepted`/`error`). |
| Certificate | `CausalCertificateProcess` pri 50; uses `action.selected` + `reward.received`. |
| Agency | `AgencyAuditProcess` pri 49 period 4. |

## P0 vs P1 deltas

| Item | P0 | P1 |
|------|----|----|
| Protocol class | none (duck type only) | `EnvironmentProtocol` wrapping the same names |
| PFC catalog | `ROOM_ACTION_SCHEMAS` inside deliberation | catalog in `legacy_action_adapter`; PFC uses schemas |
| Motor | `world.apply_action` directly | same call, wrapped as `ActionOutcome` |
| `action.selected` payload | `action`, scores, candidates | also `selected_action_id`, `candidate_action_ids` (hash uses only `tick/type/action`) |
| Facade `available_actions` | missing | still missing (intentional) |

Conceptual names from the P1 prompt (`perceive`, `describe_action`) were **not** adopted. The live names already matched the architecture.
