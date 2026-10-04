"""Cognitive stress testing — trait sweeps and grids."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nexo_qa.population.models import CohortSpec, PopulationSpec


@dataclass
class StressAxis:
    trait: str
    levels: tuple[float | int, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"trait": self.trait, "levels": list(self.levels)}


@dataclass
class CognitiveStressTest:
    stress_test_id: str
    task_id: str
    axes: tuple[StressAxis, ...]
    seeds_per_cell: int = 3
    master_seed: int = 42

    def manifest(self) -> dict[str, Any]:
        cells = 1
        for axis in self.axes:
            cells *= len(axis.levels)
        return {
            "stress_test_id": self.stress_test_id,
            "task_id": self.task_id,
            "axes": [a.to_dict() for a in self.axes],
            "seeds_per_cell": self.seeds_per_cell,
            "total_planned_runs": cells * self.seeds_per_cell,
        }

    def to_population_spec(self, population_id: str | None = None) -> PopulationSpec:
        """One-factor-at-a-time cohorts per axis level."""
        cohorts: list[CohortSpec] = []
        for axis in self.axes:
            for level in axis.levels:
                cohorts.append(
                    CohortSpec(
                        cohort_id=f"{axis.trait}_{level}",
                        label=f"{axis.trait}={level}",
                        persona_presets=("baseline",),
                        seed_count=self.seeds_per_cell,
                        task_ids=(self.task_id,),
                        metadata={"stress_trait": axis.trait, "stress_level": level},
                    )
                )
        return PopulationSpec(
            population_id=population_id or self.stress_test_id,
            master_seed=self.master_seed,
            tasks=(self.task_id,),
            cohorts=tuple(cohorts),
            metadata={"stress_test": self.manifest()},
        )


def wm_sweep(*, task_id: str = "memory_task", capacities: tuple[int, ...] = (3, 4, 5, 6, 7)) -> CognitiveStressTest:
    return CognitiveStressTest(
        stress_test_id="wm_stress",
        task_id=task_id,
        axes=(StressAxis(trait="working_memory_capacity", levels=capacities),),
    )
