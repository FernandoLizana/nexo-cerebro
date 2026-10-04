# P7 — Resource Budget

`ExecutionBudget` controls cost and safety:

| Field | Default | Role |
|-------|---------|------|
| `max_parallel_runs` | 1 | Bounded concurrency (hard cap 4 in runner) |
| `max_runs` | 500 | Reject oversized plans |
| `max_runtime_seconds` | 3600 | Policy metadata |
| `max_retries_infra` | 1 | Infrastructure only |
| `artifact_retention` | `SUMMARY_PLUS_CERTIFICATES` | Storage policy |

Run explosion guard: validation rejects >50,000 planned runs.
