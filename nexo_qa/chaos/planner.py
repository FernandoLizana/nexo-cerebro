"""Chaos planner — paired baseline/perturbed RunPlans."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from nexo_qa.chaos.models import ChaosPairPlan, ChaosPlan, ChaosSpec
from nexo_qa.chaos.validation import validate_chaos_spec
from nexo_qa.personas.loader import load_preset
from nexo_qa.population.models import RunPlan
from nexo_qa.population.seeds import derive_paired_seed, derive_run_id


class ChaosPlanner:
    def plan(self, spec: ChaosSpec, *, artifact_root: Path | str) -> ChaosPlan:
        errors = validate_chaos_spec(spec)
        if errors:
            raise ValueError("; ".join(errors))
        root = Path(artifact_root)
        spec_blob = json.dumps(spec.to_dict(), sort_keys=True)
        spec_hash = hashlib.sha256(spec_blob.encode()).hexdigest()[:16]
        persona = load_preset(spec.persona_preset)
        pairs: list[ChaosPairPlan] = []
        runs: list[RunPlan] = []
        for idx, perturbation in enumerate(spec.perturbations):
            pair_id = f"pair-{hashlib.sha256(f'{spec_hash}|{perturbation.perturbation_id}'.encode()).hexdigest()[:10]}"
            seed = derive_paired_seed(
                spec.master_seed,
                pair_id=pair_id,
                task_id=spec.task_id,
                persona_id=persona.persona_id,
            )
            condition_perturbed = f"PERTURBED_{perturbation.perturbation_id}"
            baseline_run_id = derive_run_id(
                spec_hash,
                spec.cohort_id,
                spec.task_id,
                persona.persona_id,
                seed,
                "BASELINE",
                idx * 2,
            )
            perturbed_run_id = derive_run_id(
                spec_hash,
                spec.cohort_id,
                spec.task_id,
                persona.persona_id,
                seed,
                condition_perturbed,
                idx * 2 + 1,
            )
            versions = {
                "metrics": spec.metrics_version,
                "failures": spec.failure_taxonomy_version,
                "code": spec.code_version,
                "chaos_schema": str(spec.schema_version),
            }
            baseline = RunPlan(
                run_id=baseline_run_id,
                population_id=spec.chaos_id,
                cohort_id=spec.cohort_id,
                task_id=spec.task_id,
                persona_id=persona.persona_id,
                persona_config_hash=persona.config_hash(),
                seed=seed,
                condition_set_id="BASELINE",
                sample_index=idx * 2,
                config_versions=versions,
                artifact_path=str(root / "runs" / baseline_run_id),
                pair_id=pair_id,
                pair_role="baseline",
                perturbation_id=None,
            )
            perturbed = RunPlan(
                run_id=perturbed_run_id,
                population_id=spec.chaos_id,
                cohort_id=spec.cohort_id,
                task_id=spec.task_id,
                persona_id=persona.persona_id,
                persona_config_hash=persona.config_hash(),
                seed=seed,
                condition_set_id=condition_perturbed,
                sample_index=idx * 2 + 1,
                config_versions=versions,
                artifact_path=str(root / "runs" / perturbed_run_id),
                pair_id=pair_id,
                pair_role="perturbed",
                perturbation_id=perturbation.perturbation_id,
            )
            pairs.append(
                ChaosPairPlan(
                    pair_id=pair_id,
                    perturbation=perturbation,
                    baseline_run_id=baseline_run_id,
                    perturbed_run_id=perturbed_run_id,
                    task_id=spec.task_id,
                    persona_id=persona.persona_id,
                    seed=seed,
                    condition_perturbed=condition_perturbed,
                )
            )
            runs.extend([baseline, perturbed])
        return ChaosPlan(
            chaos_id=spec.chaos_id,
            spec_hash=spec_hash,
            pairs=tuple(pairs),
            runs=tuple(runs),
        )

    def dry_run_report(self, spec: ChaosSpec) -> dict:
        n = len(spec.perturbations)
        return {
            "chaos_id": spec.chaos_id,
            "paired": spec.paired,
            "baseline_runs": n,
            "perturbed_runs": n,
            "pairs": n,
            "total_runs": n * 2,
            "dry_run": True,
        }
