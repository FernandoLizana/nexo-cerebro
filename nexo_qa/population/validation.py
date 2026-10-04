"""Population spec validation."""

from __future__ import annotations

from nexo_qa.population.models import PopulationSpec


def validate_population_spec(spec: PopulationSpec) -> list[str]:
    errors: list[str] = []
    if not spec.population_id:
        errors.append("population_id required")
    if not spec.cohorts:
        errors.append("at least one cohort required")
    total = estimate_run_count(spec)
    if total > spec.execution_budget.max_runs:
        errors.append(f"run count {total} exceeds max_runs {spec.execution_budget.max_runs}")
    if total > 50_000:
        errors.append(f"run explosion guard: {total} > 50000")
    for cohort in spec.cohorts:
        if cohort.weight < 0:
            errors.append(f"cohort {cohort.cohort_id}: negative weight")
        if not cohort.persona_presets and spec.persona_source == "preset":
            errors.append(f"cohort {cohort.cohort_id}: persona_presets required in preset mode")
    return errors


def estimate_run_count(spec: PopulationSpec) -> int:
    total = 0
    for cohort in spec.cohorts:
        personas = max(1, len(cohort.persona_presets))
        seeds = max(1, cohort.seed_count)
        tasks = max(1, len(cohort.task_ids))
        conditions = max(1, len(cohort.conditions))
        total += personas * seeds * tasks * conditions * max(1, spec.runs_per_cell)
    return total
