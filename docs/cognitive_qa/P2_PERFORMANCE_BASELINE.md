# P2 — Performance baseline

CPU-only, headless Chromium, Windows local run:

| Metric | ~seconds |
|--------|----------|
| Browser startup | 0.69 |
| Snapshot | 0.006 |
| Action generation | negligible |
| Single action execution | 0.064 |
| Integrated 64 ticks + browser | 1.06 |

RAM not sampled (`psutil` not a dependency).

See `artifacts/p2/performance.json`.
