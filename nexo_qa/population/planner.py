"""Population planner — spec → deterministic RunPlan[]."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from nexo_qa.personas.loader import load_preset
from nexo_qa.population.models import PopulationSpec, RunPlan
from nexo_qa.population.seeds import derive_child_seed, derive_run_id
from nexo_qa.population.validation import estimate_run_count, validate_population_spec


@dataclass
class PopulationPlan:
    population_id: str
    spec_hash: str
    planned_runs: int
    runs: tuple[RunPlan, ...]

    def plan_hash(self) -> str:
        import hashlib

        blob = json.dumps([r.to_dict() for r in self.runs], sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "population_id": self.population_id,
            "spec_hash": self.spec_hash,
            "plan_hash": self.plan_hash(),
            "planned_runs": self.planned_runs,
            "runs": [r.to_dict() for r in self.runs],
        }

    def write_json(self, path: Path | str) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def from_dict(cls, data: dict) -> PopulationPlan:
        runs = tuple(RunPlan.from_dict(r) for r in data.get("runs") or [])
        return cls(
            population_id=str(data["population_id"]),
            spec_hash=str(data.get("spec_hash", "")),
            planned_runs=int(data.get("planned_runs", len(runs))),
            runs=runs,
        )

    @classmethod
    def load_json(cls, path: Path | str) -> PopulationPlan:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


class PopulationPlanner:
    def plan(self, spec: PopulationSpec, *, artifact_root: Path | str) -> PopulationPlan:
        errors = validate_population_spec(spec)
        if errors:
            raise ValueError("; ".join(errors))
        root = Path(artifact_root)
        spec_hash = spec.spec_hash()
        runs: list[RunPlan] = []
        sample_counter = 0
        for cohort in spec.cohorts:
            presets = list(cohort.persona_presets) or ["baseline"]
            for task_id in cohort.task_ids:
                for condition_id in cohort.conditions:
                    for seed_idx in range(cohort.seed_count):
                        for persona_name in presets:
                            for rep in range(max(1, spec.runs_per_cell)):
                                persona = load_preset(persona_name)
                                seed = derive_child_seed(
                                    spec.master_seed,
                                    cohort_id=cohort.cohort_id,
                                    task_id=task_id,
                                    sample_index=sample_counter,
                                    persona_id=persona.persona_id,
                                    condition_set_id=condition_id,
                                )
                                run_id = derive_run_id(
                                    spec_hash,
                                    cohort.cohort_id,
                                    task_id,
                                    persona.persona_id,
                                    seed,
                                    condition_id,
                                    sample_counter,
                                )
                                artifact_path = str(root / "runs" / run_id)
                                runs.append(
                                    RunPlan(
                                        run_id=run_id,
                                        population_id=spec.population_id,
                                        cohort_id=cohort.cohort_id,
                                        task_id=task_id,
                                        persona_id=persona.persona_id,
                                        persona_config_hash=persona.config_hash(),
                                        seed=seed,
                                        condition_set_id=condition_id,
                                        sample_index=sample_counter,
                                        config_versions={
                                            "metrics": spec.metrics_version,
                                            "failures": spec.failure_taxonomy_version,
                                            "persona_schema": str(spec.persona_schema_version),
                                            "code": spec.code_version,
                                        },
                                        artifact_path=artifact_path,
                                    )
                                )
                                sample_counter += 1
        runs_sorted = tuple(sorted(runs, key=lambda r: r.run_id))
        return PopulationPlan(
            population_id=spec.population_id,
            spec_hash=spec_hash,
            planned_runs=len(runs_sorted),
            runs=runs_sorted,
        )

    def dry_run_report(self, spec: PopulationSpec) -> dict:
        return {
            "population_id": spec.population_id,
            "estimated_runs": estimate_run_count(spec),
            "max_runs": spec.execution_budget.max_runs,
            "execution_policy": spec.execution_policy,
            "dry_run": True,
        }
