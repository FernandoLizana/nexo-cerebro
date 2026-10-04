# P1 — MockWorld

Infrastructure for validating the environment contract. **Not a product.**

Module: `nexo_qa/testing/mock_world.py`

Bound with `nexo_qa.testing.bind_world(runtime, world)` after `IntegratedRuntime` construction (adapter boundary, not PFC).

## Purpose

Show that the Cognitive Core can run a domain that is **not** RoomWorld and **not** a browser, with a catalog that changes over time.

## Determinism

No RNG. Same seed/config/initial `phase` → same transitions. Cognition still uses `RandomStreams` inside `ActionGate`; two MockWorld runs with seed 42 share `trajectory_hash`.

## States

| phase | percepts | actions |
|-------|----------|---------|
| `closed` | panel, switch | `inspect_panel`, `wait` |
| `armed` | panel, switch (higher switch salience) | `activate_switch`, `step_back` |
| `open` | target | `collect_target`, `step_back` |
| `done` | complete | `finish` |

## Transitions / rewards

| from | action | to | reward |
|------|--------|----|--------|
| closed | inspect_panel | armed | 0.2 |
| closed | wait | closed | 0.01 |
| armed | activate_switch | open | 0.45 |
| open | collect_target | done | 0.8 |
| armed/open | step_back | closed | 0.02 |
| done | finish | done | 0.1 |
| any | unavailable id | unchanged | 0.0, `accepted=False`, `error=action_unavailable` |

## Success / failure

- Success (test): at least two decisions, a state transition, outcome back to the agent, certificates + agency events when those modes are integrated.
- Observed seed 42, 16 ticks, integrated executive: `inspect_panel → activate_switch → collect_target → finish…`, `phase_end=done`.

## Seed

Constructor field `seed` is recorded for reproducibility tests; MockWorld itself does not sample it.
