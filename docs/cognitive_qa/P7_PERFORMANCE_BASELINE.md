# P7 — Performance Baseline

Measured via `scripts/generate_p7_artifacts.py` with `trace_fixture` backend:

- 10-run baseline population: sub-second on dev hardware
- Aggregation included in runner elapsed time
- Parallelism capped at 4 workers; default sequential

Browser-backed populations expected slower; use bounded parallelism and retention policies.

See `artifacts/p7/performance.json`.
