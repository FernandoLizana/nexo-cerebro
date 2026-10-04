# P2 — Test report

| Suite | Passed | Failed |
|-------|--------|--------|
| P2 browser (`@pytest.mark.browser`) | 11 | 0 |
| P1 regression (with P2 phase bump) | 26 | 0 |
| v90 golden hash | match | — |

## P2 tests

- `test_playwright_driver_smoke`
- `test_browser_snapshot_visible_elements`
- `test_browserworld_generates_actions_from_visible_state`
- `test_browserworld_executes_selected_action`
- `test_browserworld_state_transition`
- `test_selector_secrecy`
- `test_navigation_policy_block`
- `test_browser_resource_cleanup`
- `test_first_autonomous_web_loop`
- `test_browserworld_agency_alternatives_on_plan_page`
- `test_three_worlds_one_brain`

CI: browser job is `continue-on-error: true` so missing Chromium does not block core regression.
