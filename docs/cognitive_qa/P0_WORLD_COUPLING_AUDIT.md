# P0 — World coupling audit

**Rule:** DOCUMENT ONLY. No decoupling in P0.

Severity: CRITICAL / HIGH / MEDIUM / LOW.

| archivo | clase/función | líneas ~ | tipo | sev | impacto futuro | recomendación P1+ |
|---------|---------------|----------|------|-----|----------------|-------------------|
| `nexo/demo/room_scenario.py` | `RoomWorld` | 10–112 | catálogo simbólico food/caregiver/danger | CRITICAL | todo el loop nexo es este toy | World protocol; RoomWorld como adapter demo |
| `nexo/demo/world_factory.py` | `create_world` | 14–27 | retorno tipado `RoomWorld` | HIGH | mundos nuevos deben subclass RoomWorld | devolver Protocol, no RoomWorld |
| `nexo/integrated_runtime.py` | `IntegratedRuntime.world` | ~223 | campo `RoomWorld` | HIGH | runtime acoplado al demo | tipo genérico |
| `nexo/prefrontal/deliberation.py` | `ROOM_ACTION_SCHEMAS`, `_pfc_score` | 1, 9–16, 47–50 | PFC conoce eat/flee/inspect | CRITICAL | no puede puntuar acciones web | puntuar desde `action_info` + drives |
| `nexo/homeostasis/drives.py` | `DriveField.action_bias` | 53–63 | drive→nombre de acción demo | CRITICAL | acciones nuevas sesgo 0 | bias por modalidad/affordance |
| `nexo/planning/goal_stack.py` | `ROOM_PLANS` | 7–11 | planes eat/flee/rest | HIGH | seek_shelter/drink no planificables | goals como needs |
| `nexo/core/process_executive.py` | `GoalStackProcess` | 57–60 | `push_plan("eat"|"flee")` | HIGH | goals = verbos demo | needs |
| `nexo/workspace/global_workspace.py` | `ROOM_ACTION_HINTS` | 11–20 | modality→verbos | HIGH | workspace solo hint RoomWorld | hints desde world |
| `nexo/core/process.py` | `AttentionProcess` | 106–107 | `food` + goal `eat` | MEDIUM | atención atada a comida | tags del world |
| `nexo/core/process_perception.py` | `PredictiveAttentionProcess` | 210–215 | food/eat, danger, distractor | MEDIUM | idem | idem |
| `nexo/thalamus/reticular.py` | `mask` | 24–29 | food/eat, danger, distractor | MEDIUM | tálamo conoce demo | goal tags |
| `nexo/homeostasis/allostasis.py` | `goal_events` | 38–45 | goals `"eat"`/`"rest"` | HIGH | need colisiona con action id | `seek_energy` vs `eat` |
| `nexo/body/metabolism.py` | `apply_action` | 50–59 | eat/rest/caregiver especiales | HIGH | acciones desconocidas solo ActionCost | costos del world |
| `nexo/body/body_state.py` | `action_costs` | 75–80 | tabla de 6 acciones | HIGH | nuevas acciones costo vacío | costos dinámicos |
| `nexo/basal_ganglia/gate.py` | `ActionGate.select` | 53, 60 | fallback `"rest"` | MEDIUM | mundos sin rest igual eligen rest | noop / first available |
| `nexo/core/process_memory.py` | `HippocampalEncoderProcess` | ~105 | siempre encode eat/flee | MEDIUM | salience = esos nombres | encode por reward/surprise |
| `nexo/social/theory_of_mind.py` | social bias | 51–72 | `approach_caregiver` | MEDIUM | social = un verbo | modalidad social |
| `nexo/language/composer.py` | utterances | 54–61 | eat/rest/caregiver | LOW | speech demo | templates desde action_info |
| `nexo/behavioral/metrics.py` | `compute_metrics` | 31–41 | eat/flee/explore ratios | HIGH | batería no puntúa mundos nuevos | métricas por task spec |
| `nexo/demo/world2d_legacy_env.py` | `apply_action` | 124–152 | x += 14; eat sin fridge | CRITICAL | “2D nav” no es física World2D | mapear a apply_motor |
| `nexo/demo/world2d_lite.py` | `apply_action` | 62–112 | mismo catálogo + x | CRITICAL | RoomWorld con contador x | idem |
| `nexo/demo/world2d_headless.py` | `apply_action` | 38–45 | explore → `step_toward` | HIGH | otras acciones siguen simbólicas | mapear todas |
| `nexo/demo/world_demo_facade.py` | `WorldDemoFacade` | 12–92 | comparte `brain.world` y aún `apply_action` | CRITICAL | dos autoridades motoras | un motor |
| `nexo/demo/world2d_actions.py` | `LEGACY_TO_INTEGRATED` | 5–38 | drink→rest, cook→eat, unknown→explore | CRITICAL | pérdida semántica | conservar keys o adapter real |
| `brain/world.py` | `_build_home`, `_interact` | 129–167, 850–1023 | fridge=eat, bed=rest, rooms | CRITICAL | casa = ontología | affordances de objeto |
| `brain/deliberation.py` | `ACTION_SCHEMAS` | 22–41 | eat/drink/study/companion | CRITICAL | deliberación = demo hogar | schemas desde world |
| `brain/agent_loop.py` | `_phase_act` | 414–497 | walk_goal + apply_motor | HIGH | navegación GPS a muebles | affordances aprendidas |
| `nexo/core/process.py` | `LegacyBrainAdapterProcess` | 308–351 | `world_tick` puede doble-step | CRITICAL | dos motores/tick | `suppress_legacy_world_tick` por defecto |

## Counts (this audit)

- CRITICAL: 9
- HIGH: 11
- MEDIUM: 6
- LOW: 1

P0 **did not** change any of these call sites.
