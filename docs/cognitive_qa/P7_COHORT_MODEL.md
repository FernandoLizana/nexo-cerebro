# P7 — Cohort Model

`CohortSpec` groups runs for aggregation and comparison:

- `persona_presets` — P5 preset names
- `seed_count` / `seed_start` — stochastic spread within cohort
- `task_ids` — tasks (no cross-task mixing without explicit labels)
- `conditions` — e.g. `BASELINE` (P8 will add `INTERRUPTED`, etc.)
- `weight` — sampling weight metadata (not demographic claim)

Cohorts are **experimental segments**, not demographic groups.
