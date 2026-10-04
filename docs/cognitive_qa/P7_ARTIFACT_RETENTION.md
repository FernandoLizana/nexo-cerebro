# P7 — Artifact Retention

Default: `SUMMARY_PLUS_CERTIFICATES` — per-run `cognitive_qa_report.json`, certificates, optional raw trace.

Population layout:

```text
artifacts/p7/populations/<population_id>/
  population_plan.json
  population_state.json
  population_report.json
  population_report.md
  runs.csv
  runs/<run_id>/raw_trace.json
  runs/<run_id>/cognitive_qa_report.json
  aggregates/cohorts.json
  aggregates/failures.json
```

Large populations should not retain per-tick screenshots; failure keyframes only when browser backend is used.
