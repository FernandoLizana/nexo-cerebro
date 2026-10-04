# P3 — Test report

**Date:** 2026-08-19 · **Verdict:** PASS

## P3 tests (20/20)

| # | Test | Result |
|---|------|--------|
| 1 | `test_hybrid_scene_contains_visible_geometry` | PASS |
| 2 | `test_offscreen_target_not_perceived_before_scroll` | PASS |
| 3 | `test_scroll_reveals_new_percept` | PASS |
| 4 | `test_modal_occludes_background_actions` | PASS |
| 5 | `test_salience_reflects_controlled_visual_difference` | PASS |
| 6 | `test_dense_region_has_higher_visual_clutter` | PASS |
| 7 | `test_perceptual_diff_detects_new_error` | PASS |
| 8 | `test_duplicate_labels_keep_distinct_identity` | PASS |
| 9 | `test_selector_secrecy_scene_serialization` | PASS |
| 10 | `test_element_action_requires_eligible_percept` | PASS |
| 11 | `test_dom_fast_vs_hybrid_differ` | PASS |
| 12 | `test_perceptual_autonomous_loop` | PASS |
| 13 | `test_distractor_behavior_salience` | PASS |
| 14 | `test_attention_integration_changes_attended_set` | PASS |
| 15 | `test_no_action_on_hidden_element` | PASS |
| 16 | `test_no_action_on_disabled_button` | PASS |
| 17 | `test_focus_boost_on_input` | PASS |
| 18 | `test_modal_focus_dominates_actions` | PASS |
| 19 | `test_hybrid_scene_reproducibility` | PASS |
| 20 | `test_p3_legacy_regression_dom_fast_still_works` | PASS |

## Regression

- P2 browser: 11/11
- P1 contract: PASS
- v90 golden (seed 42, 12 ticks): unchanged

Run: `pytest tests/test_p3_perception.py -m browser`
