# P0 — Current environment contract (agent ↔ world)

`nexo/environment.py` is **not** this contract. It captures git/Python/platform metadata (`capture_environment`, `write_environment_files`).

There is **no World ABC**. The live nexo contract is duck-typed on `runtime.world` / `scheduler.config["world_state"]`.

## Two loops

| Loop | Entry | Perceive | Decide | Act |
|------|-------|----------|--------|-----|
| Integrated | `IntegratedRuntime.run` → `CognitiveScheduler.step` | `world.percepts_for_agent()` | PFC + `ActionGate` → `action.selected` | `MotorExecutionProcess` → `world.apply_action` |
| Legacy | `InfantApeBrain.world_tick` → `NeuralAgentLoop.run` | `_world_sensory` / vision | `brain.deliberation.PrefrontalDeliberation.run` writes `choice_key` | `World2D.apply_motor` |

v90 uses `world_mode: world_demo_facade` (`WorldDemoFacade`) sharing `brain.world`, but nexo **still** calls `apply_action`, not `apply_motor`, unless a specific world maps explore → `step_toward`.

## Duck-typed methods (real names)

Implemented by `RoomWorld` (`nexo/demo/room_scenario.py`) and subclasses/facades from `nexo/demo/world_factory.py` → `create_world`.

| FILE | CLASS | METHOD | INPUT | OUTPUT | SIDE EFFECTS |
|------|-------|--------|-------|--------|--------------|
| `nexo/demo/room_scenario.py` | `RoomWorld` | `percepts_for_agent` | none | `list[tuple[str, float, tuple[float, ...]]]` modality/salience/embedding | read-only |
| same | `RoomWorld` | `available_actions` | none | `tuple[str, ...]` | none |
| same | `RoomWorld` | `action_info` | `action: str` | `dict` with `base_value`, `cost_energy`, `risk`, `modality` | none |
| same | `RoomWorld` | `apply_action` | `action: str` | `{reward, homeostatic_deltas, encoded_memory}` | mutates food/danger/trust/history |
| same | `RoomWorld` | `sync_from_body` | body object | none | copies `body.energy` → `world.energy` |

Factory: `nexo/demo/world_factory.create_world(mode, seed=42) -> RoomWorld`.

Callers (nexo):

| Role | FILE | CLASS.METHOD |
|------|------|----------------|
| Inject world | `nexo/integrated_runtime.py` | `IntegratedRuntime.__post_init__` (`config["world_state"]`) |
| Perceive | `nexo/core/process_perception.py` | `RawSensoryCaptureProcess.step` |
| Perceive (legacy mode) | `nexo/core/process.py` | `SensoryRelayProcess.step` |
| Candidates | `nexo/core/process_executive.py` | `PrefrontalDeliberationProcess.step`, `EnhancedBasalGangliaProcess.step` |
| Candidates | `nexo/core/process.py` | `BasalGangliaSelectorProcess.step` |
| Execute | `nexo/core/process.py` | `MotorExecutionProcess.step` → `world.apply_action` |

## Conceptual flow (v90 integrated)

```text
CognitiveScheduler.step
   ↓ priority 92 RawSensoryCaptureProcess  world.percepts_for_agent()
   ↓ 88–87 thalamus + PredictiveHierarchy   perception.updated
   ↓ 86–75 metabolism / interoception / sleep / allostasis
   ↓ 71 GoalStackProcess
   ↓ 70 PredictiveAttentionProcess
   ↓ 63 PrefrontalDeliberationProcess        ROOM_ACTION_SCHEMAS ∩ available_actions
   ↓ 61 TDBiasProcess
   ↓ 60 EnhancedBasalGangliaProcess          ActionGate.select → action.selected
   ↓ 58 UnifiedMotorProcess                  AUDIT ONLY (unified.motor)
   ↓ 56 CerebellarCorrectionProcess          may set config["motor_action"]
   ↓ 55 MotorExecutionProcess                world.apply_action + reward.received
   ↓ 53 TDLearningProcess
   ↓ 52 HippocampalEncoderProcess
   ↓ 50 CausalCertificateProcess
   ↓ 49 AgencyAuditProcess (every 4 ticks)
   ↓ clock.advance(1)
```

## Conceptual names vs reality

P0 asked for something like `percepts_for_agent` / `available_actions` / `action_info` / `apply_action`. **Those are the real names** on `RoomWorld`. Do not invent a protocol class until P1.

Legacy brain does **not** implement this duck type. It uses `World2D.apply_motor` (`brain/world.py`).
