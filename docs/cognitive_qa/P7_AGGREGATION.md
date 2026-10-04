# P7 — Aggregation

`PopulationAggregator` produces `PopulationResult` and `CohortResult`:

- **Distributions:** mean, median, percentiles (p10–p90) for NCFS, CRS, EHFP
- **Denominators:** `n_valid`, `valid_runs_denominator` per cohort
- **Small N:** `INSUFFICIENT_SAMPLE` when n < 5
- **Coverage:** planned / completed / valid / infra failures
- **Disclaimer** on every result dict

Missing metrics are omitted, not coerced to zero.
