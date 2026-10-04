# P4 — Overview

**Phase:** P4 · **Theme:** Goal Semantics, Task Context, Autonomous Objective Reasoning  
**Verdict:** PASS · **Date:** 2026-08-19

## Mission

NEXO receives a **declarative high-level goal** and uses it as **active intention** to steer perception (via existing P3 path), deliberation, and action — **without** a correct step sequence from the test harness.

## Before / after

### Before (P3)

```text
BrowserWorld.goal: str  # stored, never read by PFC
PerceptualScene → actions → NEXO (homeostatic goals only)
P2_LIMITATION_GOAL_SEMANTICS
```

### After (P4)

```text
Goal + TaskContext
  → TaskGoalProcess
  → goals.updated / goal.progress / goal.relevance
  → PrefrontalDeliberator (+ goal_relevance)
  → action → evaluate_progress → next decision
```

## Architecture

```text
                    TASK GOAL (NL)
                          │
                   parse_goal()
                          │
              ┌───────────┴───────────┐
              │                       │
         TaskContext              Goal entities
         (agent data)            constraints
              │                       │
              └───────────┬───────────┘
                          │
                  TaskGoalProcess
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
  goals.updated    goal.relevance    goal.progress
         │                │                │
         └────────────────┼────────────────┘
                          ▼
              PrefrontalDeliberator / BG
                          │
                    BrowserWorld
                   (P3 PerceptualScene)
                          │
                      Web Lab
```

## Golden rules

| Rule | Status |
|------|--------|
| GOAL ≠ SCRIPT | Enforced |
| ORACLE ≠ PLANNER | Enforced |
| WEB_CONTENT ≠ TASK_GOAL | Enforced |
| Action requires perception (P3) | Preserved |

## Module map

| Path | Role |
|------|------|
| `nexo_qa/goals/` | Models, parser, relevance, progress, runtime |
| `nexo_qa/scenarios/task_definition.py` | Declarative tasks |
| `nexo_qa/scenarios/oracle.py` | Test-only predicates |
| `nexo/prefrontal/deliberation.py` | `goal_relevance` boost |
| `nexo/core/process_executive.py` | BG relevance boost |

## Documentation index

| Doc | Topic |
|-----|-------|
| [P4_GOAL_MODEL.md](P4_GOAL_MODEL.md) | Goal lifecycle |
| [P4_TASK_CONTEXT.md](P4_TASK_CONTEXT.md) | Agent-visible data |
| [P4_GOAL_PARSER.md](P4_GOAL_PARSER.md) | Limited NL |
| [P4_PROGRESS_MODEL.md](P4_PROGRESS_MODEL.md) | Evidence-based progress |
| [P4_GOAL_RELEVANCE.md](P4_GOAL_RELEVANCE.md) | Relevance → PFC |
| [P4_SUBGOALS_AND_RECOVERY.md](P4_SUBGOALS_AND_RECOVERY.md) | Loops, wrong choices |
| [P4_ORACLE_SEPARATION.md](P4_ORACLE_SEPARATION.md) | Test vs runtime |
| [P4_INSTRUCTION_AUTHORITY.md](P4_INSTRUCTION_AUTHORITY.md) | Authority hierarchy |
| [P4_WEB_LAB.md](P4_WEB_LAB.md) | Scenarios |
| [P4_TEST_REPORT.md](P4_TEST_REPORT.md) | 22 tests |
| [P4_REGRESSION_REPORT.md](P4_REGRESSION_REPORT.md) | Gates A–K |
| [P4_PERFORMANCE_BASELINE.md](P4_PERFORMANCE_BASELINE.md) | Overhead |
| [P4_RISKS_AND_DEBT.md](P4_RISKS_AND_DEBT.md) | Limitations |
| [P4_HANDOFF_TO_P5.md](P4_HANDOFF_TO_P5.md) | Personas next |

## ADR

[ADR-0005](adr/ADR-0005-goal-semantics-task-context.md)

## Next

P5 — Cognitive Personas / Individual Differences (same goal, same page, different profile → different behavior).
