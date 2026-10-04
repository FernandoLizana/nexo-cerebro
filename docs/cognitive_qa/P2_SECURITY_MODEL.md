# P2 — Security model

Module: `nexo_qa/browser/policy.py`

| Control | Default |
|---------|---------|
| Allowed origins | `http://127.0.0.1:*`, `http://localhost:*` |
| External navigation | blocked → `POLICY_BLOCKED` |
| Downloads | disabled |
| File upload | disabled |
| Real credentials | forbidden in lab |
| NEXO-generated JS eval | forbidden |

Blocked navigation returns structured outcome, not core crash.

Tests: `test_navigation_policy_block`, `test_selector_secrecy`
