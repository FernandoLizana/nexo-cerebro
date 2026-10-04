# P3 — Performance baseline

Measured on Web Lab `index.html` (5 snapshots each):

| Mode | Avg ms | Notes |
|------|--------|-------|
| DOM_FAST | ~10.4 | P2 baseline |
| HYBRID | ~9.3 | Includes occlusion + style reads |
| Ratio | ~0.9× | Below 10× alert threshold |

Hybrid is not orders of magnitude slower on simple pages. Full loop overhead dominated by Playwright I/O, not salience math.

See `artifacts/p3/quality_gate.json` for captured values.
