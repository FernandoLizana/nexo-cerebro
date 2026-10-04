# P8 — Perturbation Model

`PerturbationSpec` (`nexo_qa/chaos/models.py`):

| Field | Role |
|-------|------|
| `perturbation_id` | Stable ID |
| `type` | INTERRUPTION, LATENCY, TRANSIENT_ERROR, … |
| `trigger` | AT_TICK, AFTER_ACTION, … |
| `intensity` / `duration_ticks` | Controlled magnitude |
| `target_scope` | Must be `environment` |
| `parameters` | Type-specific env params |
| `seed` | For seeded probabilistic triggers |

Validation: `validate_perturbation_spec()` — rejects non-environment scope.

Config: `configs/nexo_qa/chaos/paired_baseline.yaml`
