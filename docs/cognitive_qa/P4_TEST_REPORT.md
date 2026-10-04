# P4 — Test report

**Date:** 2026-08-19 · **File:** `tests/test_p4_goals.py` · **Verdict:** 22/22 PASS

Requires: `pip install -e ".[browser]"` + `playwright install chromium`

## Test catalog

| # | Test | Category |
|---|------|----------|
| 1 | `test_goal_parser_extracts_basic_intent_and_entities` | Parser |
| 2 | `test_goal_does_not_contain_steps` | Goal model |
| 3 | `test_task_context_leakage` | Task context |
| 4 | `test_goal_activation_pending_to_active` | Activation |
| 5 | `test_progress_partial_one_constraint_satisfied` | Progress |
| 6 | `test_progress_non_monotonic_plan_change` | Progress |
| 7 | `test_subgoal_creation_from_semantics_not_scenario` | Subgoals |
| 8 | `test_no_hardcoded_scenario_plan_in_runtime` | Anti-cheat |
| 9 | `test_goal_relevance_prefers_plan_pro` | Relevance |
| 10 | `test_offscreen_still_offscreen_despite_goal` | P3 invariant |
| 11 | `test_distractor_salience_vs_goal_relevance` | Relevance vs salience |
| 12 | `test_register_pro_autonomous_attempt` | Autonomy |
| 13 | `test_find_pricing_autonomous` | Navigation goal |
| 14 | `test_wrong_choice_recovery_no_auto_correct` | Recovery |
| 15 | `test_blocked_goal_policy` | Policy |
| 16 | `test_loop_detection` | Loop |
| 17 | `test_goal_drift_detection` | Stagnation |
| 18 | `test_goal_causal_trace_events` | Causality |
| 19 | `test_agency_goal_given_path_not_given` | Agency |
| 20 | `test_adversarial_web_does_not_mutate_task_goal` | Instruction authority |
| 21 | `test_p4_legacy_regression_dom_fast` | P3/P2 regression |
| 22 | `test_task_goal_process_emits_relevance` | Integration |

## Regression bundled in CI (optional steps)

- P3: `tests/test_p3_perception.py`
- P2: `tests/test_p2_browser.py`
- P4: `tests/test_p4_goals.py`

## Run commands

```bash
# Full P4
pytest tests/test_p4_goals.py -m browser -v

# Quick smoke
pytest tests/test_p4_goals.py -q -m browser

# With durations
pytest tests/test_p4_goals.py -m browser --durations=10
```

## Known non-guarantees

`test_register_pro_autonomous_attempt` asserts mechanism (actions, progress events) — **not** 100% success on all seeds for Pro completion.

## Artifacts

`artifacts/p4/preflight.json`, `artifacts/p4/quality_gate.json`
