# P3 — Web Lab

## P2 pages (unchanged)

`index.html`, `name.html`, `plan.html`, `summary.html`, `success.html`

## P3 perceptual scenarios

| Page | Scenario |
|------|----------|
| `low_salience.html` | LOW_SALIENCE_BUTTON |
| `distractor.html` | DISTRACTOR_BUTTON |
| `below_fold.html` | BELOW_THE_FOLD |
| `modal_overlay.html` | MODAL_OVERLAY |
| `dense_form.html` | DENSE_FORM |
| `error_message.html` | ERROR_MESSAGE |
| `duplicate_labels.html` | DUPLICATE_LABELS |
| `hidden_disabled.html` | Hidden/disabled audit |

## Oracle manifest

`tests/fixtures/web_lab/visual_manipulations.json` — **tests only**, never loaded by runtime.

## Server

`nexo_qa/testing/web_lab_server.py` serves fixtures on ephemeral `127.0.0.1` port.
