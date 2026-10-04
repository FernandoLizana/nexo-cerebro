# P7 — Failure Clustering

`FailureClusterer` groups failures across runs by `(family, failure_type)`:

- `simulation_prevalence` = affected runs / valid runs
- `certificate_refs` for drill-down to individual P6 certificates
- `affected_run_ids` for drill-down to runs
- `rare_critical()` preserves HIGH/CRITICAL clusters regardless of frequency

No ML clustering — deterministic taxonomy-based buckets.
