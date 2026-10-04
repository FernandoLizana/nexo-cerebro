# P1 → P2 handoff

P2 adds **BrowserWorld** as another `EnvironmentProtocol` implementation. P2 does **not** rewrite PFC, memory, TD, or certificates.

## 1. Interface BrowserWorld must implement

The live contract in `nexo/core/environment_protocol.py`:

- `percepts_for_agent()`
- `available_actions()`
- `action_info(action)`
- `apply_action(action)`
- optional `sync_from_body`
- recommended `action_schemas()` returning `ActionSchema` with locators **only in metadata or an internal map**, never scored by PFC

## 2. Percepts

Keep the generic triple `(modality, salience, embedding)`. Do not introduce `WebElementPercept` / screenshot types here — that is P3. A coarse modality such as `"panel"` / `"control"` is enough for P2 connectivity.

Proposed later (P3, not P1/P2 implementation): `DOM_FAST` / `HYBRID` / `VISION`.

## 3. Actions

Dynamic catalog from the current page: each visible control → `ActionSchema(id=stable_string, affordance="selectable"|…, action_type generic)`. **No** `if action.type == "click"` in cognition.

## 4. Hide selectors

```text
NEXO knows: id / label / affordance
BrowserWorld knows: CSS / XPath / Playwright locator
```

Store locators in an environment-private dict keyed by `ActionSchema.id`. PFC tests already forbid depending on `metadata["css_selector"]`.

## 5. Apply

`apply_action(id)` looks up the private payload, performs the side effect, returns `{reward, accepted, success, error, ...}`. Timeouts and missing controls are **domain outcomes**, not brain crashes.

## 6. Outcome

Reuse `ActionOutcome.from_apply_result`. Keep `reward.received` `payload.value` as the learning signal.

## 7. What P2 must not touch

- `configs/nexo/integrated_v90.yaml` semantics
- v90 golden hash unless a new freeze is explicit
- Memory / sleep / TD / metabolism formulas
- Adding Playwright imports to `nexo/prefrontal` or `nexo/core/action_schema.py`
- `WorldDemoFacade.available_actions` without a new golden

## 8. P1 tests that must keep passing

- `tests/test_p1_action_schema.py`
- `tests/test_p1_environment_contract.py`
- `tests/test_p1_two_worlds_one_brain.py`
- `tests/test_p0_nexo_qa_import.py`
- `tests/test_executive_integrated.py::test_pfc_veto_inhibits_distractor_when_low_energy`
- P0 smoke: `test_integrated_core`, `test_reproducibility`, `test_body_homeostasis`, sprints 71–78
- v90 `runtime_from_config` + `run(ticks=12)` hash

## 9. Left for P3

Web perception fidelity, screenshots, OCR, accessibility tree richness, Cognitive Personas, friction scores.

## Bind pattern (already used)

```python
rt = IntegratedRuntime(...)
bind_world(rt, BrowserWorld(...))  # or factory; not inside PFC
rt.run()
```
