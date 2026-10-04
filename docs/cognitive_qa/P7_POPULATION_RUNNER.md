# P7 — Population Runner

`PopulationRunner` executes plans with isolation and P6 as single-run truth:

- Backends: `trace_fixture` (CI), `mock_world` (live NEXO + MockWorld)
- Per-run: `capture_run_trace` → `analyze_raw_trace` (P6)
- Statuses: `COMPLETED`, `FAILED_TASK`, `FAILED_INFRASTRUCTURE`, etc.
- **Task failures are not retried**; infrastructure failures may retry (`max_retries_infra`)
- Cache: `reuse_completed_runs` reuses existing `cognitive_qa_report.json`
- Bounded parallel via `ThreadPoolExecutor` (max 4 workers)

Runner does **not** implement metrics — it delegates to P6.
