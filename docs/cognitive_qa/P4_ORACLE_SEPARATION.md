# P4 — Oracle separation

## Principle

**ORACLE ≠ PLANNER**

The test harness may know success/failure; NEXO runtime must not.

## Architecture

```text
                  Task Definition
                    /        \
                   /          \
          Agent-visible      Test-only
              │                │
          Goal + Context     Oracle
              │                │
              ▼                ▼
             NEXO         Evaluator only
              │                │
              └──── result ────┘
```

## Agent-visible (`nexo_qa/scenarios/task_definition.py`)

- `REGISTER_PRO_GOAL` — NL description
- `REGISTER_PRO_CONTEXT` — `user_name`, `email`, `desired_plan`
- `parse_goal()` output → `bind_task()`

## Test-only (`nexo_qa/scenarios/oracle.py`)

- `success_predicate(url, required_plan=...)`
- `failure_predicate(url)`
- `expected_final_state(plan=...)`

**Never imported** by `TaskGoalProcess`, `BrowserWorld`, `PrefrontalDeliberator`, or deliberation path.

## Forbidden in runtime decision code

```text
next_correct_action
current_step
correct_button
correct_path
expected_path (in scheduler config)
ScenarioOracle (as decision input)
```

Static test: `test_no_hardcoded_scenario_plan_in_runtime`.

## Web Lab

`browser_lab.GOAL` is documentation metadata; cognition receives goal via `bind_task`, not by reading scenario modules at decision time.

## Evaluation flow (tests)

```python
# After rt.run() — test side only
from nexo_qa.scenarios.oracle import success_predicate
assert success_predicate(world._snapshot.url, required_plan="pro")
```

NEXO never sees `required_plan="pro"` as a decision hint — only as extracted entity from NL goal + TaskContext.
