# P0 — Handoff to P1

P1 starts **abstraction of the agent↔world contract**. P1 does **not** implement Playwright, personas, Cognitive Friction Score, or Browser automation.

Read first: this file + `P0_ARCHITECTURE_MAP.md` + `P0_CURRENT_ENVIRONMENT_CONTRACT.md` + golden `artifacts/baseline/p0/reproducibility/comparison.json`.

**Regression gate:** after any P1 change, `trajectory_hash` for `integrated_v90` seed 42 ticks 12 must remain equal to `run_A.json` **or** the delta must be explained as intentional with a new golden.

---

## 1. Formalize the duck-typed world as a protocol (without breaking RoomWorld)

**WHY:** cognition is typed/coupled to `RoomWorld` (`world_factory.create_world` → `RoomWorld`).

**FILES:** `nexo/demo/world_factory.py`, `nexo/demo/room_scenario.py`, `nexo/integrated_runtime.py`

**RISK:** HIGH if protocol methods change signatures.

**TESTS REQUIRED:** existing `tests/test_integrated_core.py`; new MockWorld tests only if protocol is additive.

**DEPENDENCIES:** none.

**Do not** implement BrowserWorld here. Optionally a `MockWorld` in tests that implements the same four methods.

---

## 2. Stop scoring actions from a frozen RoomWorld schema table

**WHY:** `ROOM_ACTION_SCHEMAS` cannot represent DOM actions.

**FILES:** `nexo/prefrontal/deliberation.py`, `nexo/homeostasis/drives.py` `action_bias`, `nexo/planning/goal_stack.py` `ROOM_PLANS`, `nexo/workspace/global_workspace.py` `ROOM_ACTION_HINTS`

**RISK:** CRITICAL behavioral. Expect `trajectory_hash` change if done naively.

**TESTS:** rerun P0 golden; `tests/test_sprints_75_78_integrated.py`; behavioral tasks survival/distractor.

**DEPENDENCIES:** task 1 (world still provides `available_actions` + `action_info`).

**Proposal only (do not implement in P0):**

```text
ActionSchema
├── id
├── label
├── type
├── target
├── affordance
├── expected_effect
├── estimated_cost
└── risk
```

Validate in P1 against `RoomWorld.action_info` fields (`base_value`, `cost_energy`, `risk`, `modality`).

---

## 3. Single motor authority per tick

**WHY:** facade + `LegacyBrainAdapterProcess` can double-step.

**FILES:** `nexo/core/process.py` `LegacyBrainAdapterProcess`, `nexo/demo/world_demo_facade.py`, `unified_motor_mode` / `suppress_legacy_world_tick`

**RISK:** HIGH (Flask demo feel).

**TESTS:** `tests/test_flask_unified_integrated.py`, `world_demo_facade` task.

**DEPENDENCIES:** none.

---

## 4. Replace silent key collapse in `world2d_actions`

**WHY:** drink→rest and unknown→explore hide failures that QA would want as data.

**FILES:** `nexo/demo/world2d_actions.py`

**RISK:** MEDIUM–HIGH for v90 facade (current golden is all `explore`).

**TESTS:** golden hash; world2d navigation tasks.

**DEPENDENCIES:** 2.

---

## 5. Keep Cognitive QA disabled

**WHY:** PRINCIPLE 9.

**FILES:** do **not** add a runtime flag to `IntegratedRuntimeConfig` until there is a consumer. Spec:

```yaml
cognitive_qa:
  enabled: false
```

If added later, default **false**, ignored by scientific batteries.

**TESTS:** `tests/nexo_qa/test_p0_import.py` remains the only QA test until P1 features exist.

**DEPENDENCIES:** none.

---

## Explicitly out of P1

- Playwright / Selenium / real browser
- Cognitive personas
- Human Failure Probability
- Changing memory, sleep, TD, certificate algorithms
- Completing roadmap 91/100 traceability
- Paper Adaptive Behavior
- GPU 50k

## Recommended P1 scope (exact)

1. Documented Protocol (typing) around existing duck type.  
2. MockWorld for unit tests.  
3. Design + tests for ActionSchema **fed by RoomWorld.action_info**, defaulting to current verbs so v90 golden still matches.  
4. Audit-only check that `nexo_qa` still imports and CI subset still passes.
