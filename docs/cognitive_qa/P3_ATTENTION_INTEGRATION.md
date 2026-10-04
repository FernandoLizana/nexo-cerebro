# P3 — Attention integration

## Separation

| Concept | Meaning |
|---------|---------|
| `visibility_score` | Structurally visible in viewport |
| `salience_score` | Heuristic stimulus prominence |
| `attention_tier` | FOCAL / PERIPHERAL / UNATTENDED after gate |

## Gate

`PerceptualAttentionGate` (`nexo_qa/perception/attention_gate.py`):

- Filters offscreen / near-zero visibility
- Ranks eligible percepts deterministically
- Assigns top `max_focal_percepts` as FOCAL, next as PERIPHERAL
- Records `ATTENTION_LIMIT` in `exclusion_audit`

## NEXO mapping

`BrowserWorld.percepts_for_agent()` emits tuples `(modality, salience, embedding)` from FOCAL+PERIPHERAL percepts → consumed by `RawSensoryCaptureProcess` → thalamic relay → existing attention stack.

No parallel WebAttentionEngine; minimal core changes.

## Action link

Hybrid mode: element actions only from attended, eligible percepts. Global `scroll` / `go back` exempt.
