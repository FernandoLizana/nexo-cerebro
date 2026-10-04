# P6 — Event Normalization

`CognitiveQAEvent` adapter in `nexo_qa/analysis/normalize.py`.

Sources:

- `runtime.state_store.event_log` (NEXO CognitiveEvent)
- `BrowserWorld.trace_log` (PERCEPTUAL_SCENE, ATTENTION_TRACE, WEB_OUTCOME)

Forbidden keys scrubbed: selector, xpath, data-testid, password, token, secret.

See `artifacts/p6/event_schema.json`.
