# P7 — PopulationSpec

`PopulationSpec` (`nexo_qa/population/models.py`) defines a versioned, reproducible population:

| Field | Purpose |
|-------|---------|
| `population_id` | Stable identifier |
| `master_seed` | Root for child seed derivation |
| `cohorts` | List of `CohortSpec` |
| `runs_per_cell` | Replicates per persona×seed×task×condition |
| `execution_policy` | `sequential` / `low_resource` / `bounded_parallel` |
| `execution_budget` | `max_runs`, `max_parallel_runs`, retention |
| `metrics_version` / `failure_taxonomy_version` | P6 compatibility |

YAML configs: `configs/nexo_qa/populations/*.yaml`

Validation: `validate_population_spec()` — rejects empty cohorts, run explosion (>50k), budget exceedance.
