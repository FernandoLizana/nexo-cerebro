# P1 — Risks and deferred debt

Format: `P1-RISK-XXX` · category · severity.

## P1-RISK-001 · CORE COUPLING · HIGH · DEFERRED

`WorldDemoFacade` still lacks `available_actions`. v90 integrated PFC/BG throw every tick; scheduler `except: continue`. Golden 12× explore comes from the **legacy early adapter**. Adding the method would change the hash. **Do not fix in P2 unless a new golden is declared.**

## P1-RISK-002 · ACTION MODEL · MEDIUM · DEFERRED

`ROOM_ACTION_HINTS` in `nexo/workspace/global_workspace.py` still maps modalities to RoomWorld verbs.

## P1-RISK-003 · ACTION MODEL · MEDIUM · DEFERRED

`GoalStack` `ROOM_PLANS` / `push_plan("eat"|"flee")` still name-locked.

## P1-RISK-004 · CORE COUPLING · MEDIUM · DEFERRED

Attention bonuses for `food`/`eat`; sleep path still special-cases `action == "rest"` in BG.

## P1-RISK-005 · LEGACY · HIGH · DEFERRED

`world2d_actions.py` drink→rest / unknown→explore. Changing it would alter facade semantics.

## P1-RISK-006 · ARCHITECTURE · HIGH · DEFERRED

Dual motor: facade + `LegacyBrainAdapterProcess`. `suppress_legacy_world_tick` / unified motor remain as in v90.

## P1-RISK-007 · ACTION MODEL · LOW

`ActionGate` no-go fallback still prefers `"rest"` when present. P1 only falls back to `candidates[0]` when `rest` is absent (MockWorld).

## P1-RISK-008 · CONFIGURATION · LOW · DEFERRED

`cognitive_qa.enabled` is still **not** wired into `IntegratedRuntimeConfig` / v90 YAML (P0 PRINCIPLE 9).

## P1-RISK-009 · SERIALIZATION · LOW

`IntegratedRuntime.world` type hint remains `RoomWorld` in places; runtime bind is duck-typed. Pickle paths were not moved.

## P1-RISK-010 · OBSERVABILITY · LOW

Causal certificate still omits full percepts/post-state (`P0-RISK-005`). P1 only added candidate ids on `action.selected`.

## P1-RISK-011 · TESTING · LOW

`tests/nexo_qa/` was removed because it shadowed the `nexo_qa` package. Import smoke lives at `tests/test_p0_nexo_qa_import.py`.

## P1-RISK-012 · PERFORMANCE · INFO

v90 12-tick wall time P1 ≈ 2.9–3.0 s vs P0 ≈ 3.4–3.7 s (startup included). No >15% regression. RAM not sampled (`psutil` not a dependency).

## Intentionally not changed

Memory, sleep architecture, TD equations, reward formulas, affect, ToM, publication batteries, connecting `cognitive_qa` into scientific YAML.
