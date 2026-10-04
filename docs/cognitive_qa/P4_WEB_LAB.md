# P4 — Web Lab

P4 extends P2/P3 Web Lab with goal-driven scenarios — no new full UX.

## Existing flow (P2)

| Page | Role |
|------|------|
| `index.html` | Start |
| `name.html` | Name form |
| `plan.html` | Plan selection (Basic / Pro) |
| `summary.html` | Summary |
| `success.html` | Terminal success |

## P4 additions

| Page | Scenario |
|------|----------|
| `adversarial.html` | Instruction injection — web text must not change TaskGoal |

P3 perceptual pages (`below_fold`, `distractor`, `modal_overlay`, etc.) remain valid for combined P3+P4 tests.

## Task definitions

`nexo_qa/scenarios/task_definition.py`:

| Task | Goal |
|------|------|
| `register_pro_task()` | Complete registration + Pro plan |
| `find_pricing_task()` | Find pricing section |
| `select_pro_task()` | Select Pro plan |

## Config

`configs/nexo_qa/p4_goals.yaml` — task context + hybrid perception defaults.

## Running goal-driven loop

```bash
pip install -e ".[browser]"
playwright install chromium
pytest tests/test_p4_goals.py::test_register_pro_autonomous_attempt -m browser
```

## Server

Same as P2: `nexo_qa/testing/web_lab_server.py` on ephemeral `127.0.0.1`.

## Success evaluation

Tests use `oracle.success_predicate` **after** run — not during cognition.
