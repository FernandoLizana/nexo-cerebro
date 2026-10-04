# P5 — Web Lab

## Scenarios

| ID | Fixtures | Mechanism under test |
|----|----------|---------------------|
| MEMORY_DEMAND | memory_demand_start.html, memory_demand_entry.html | WM |
| DISTRACTOR | distractor.html | distractibility |
| RISKY_CONFIRMATION | risky_confirmation.html | risk_aversion |
| LONG_FLOW | long_flow_1..4.html | patience / fatigue |
| REPEATED_FAILURE | repeated_failure.html | frustration_tolerance |
| NOVICE_NAVIGATION | novice_navigation.html | digital_literacy |
| AMBIGUOUS_UI | ambiguous_ui.html | semantic_confidence |

Manifest: `tests/fixtures/web_lab/persona_scenarios.json`

## Invariants preserved

- No selector leakage to persona configs
- No oracle in runtime
- P3 action-requires-perception unchanged
