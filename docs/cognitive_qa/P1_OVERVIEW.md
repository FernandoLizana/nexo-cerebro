# P1 — Overview

P1 separates the NEXO Cognitive Core from the demo world so the same brain can decide over **dynamic, domain-agnostic action catalogs**.

```text
                    NEXO Cognitive Core
                            │
                    EnvironmentProtocol
                            │
             ┌──────────────┴──────────────┐
             │                             │
       RoomWorld / v90                  MockWorld
         (legacy verbs)                (panel/switch)
```

## What P1 did

- Formalized `EnvironmentProtocol` around the live duck type.
- Added `ActionSchema` / `ActionOutcome`.
- Moved `ROOM_ACTION_SCHEMAS` out of PFC into `legacy_action_adapter`.
- PFC scores affordances, not RoomWorld names.
- Added deterministic `MockWorld` and `test_two_worlds_one_brain`.
- Preserved v90 golden `trajectory_hash`.

## What P1 did not do

Playwright, Selenium, BrowserWorld, personas, friction scores, LLM APIs, new pip dependencies, memory/sleep/TD formula changes, adding `available_actions` to `WorldDemoFacade`.

## Quality gates

See `artifacts/p1/quality_gate.json` and `P1_REGRESSION_REPORT.md`.

## Next

`P1_HANDOFF_TO_P2.md` — BrowserWorld as another EnvironmentProtocol implementation.
