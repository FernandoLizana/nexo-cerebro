"""Population engine models — spec, cohorts, run plans, results."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

SCHEMA_VERSION = 1
BASELINE_CONDITION = "BASELINE"

PersonaSourceMode = Literal["preset", "distribution"]
ExecutionPolicy = Literal["sequential", "low_resource", "bounded_parallel"]
ArtifactRetention = Literal["FULL", "FAILURES_ONLY", "SUMMARY_PLUS_CERTIFICATES", "MINIMAL"]


class RunStatus(str, Enum):
    PLANNED = "PLANNED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED_TASK = "FAILED_TASK"
    FAILED_INFRASTRUCTURE = "FAILED_INFRASTRUCTURE"
    BLOCKED = "BLOCKED"
    ABANDONED = "ABANDONED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class ConditionSet:
    condition_set_id: str = BASELINE_CONDITION
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"condition_set_id": self.condition_set_id, "metadata": dict(self.metadata)}


@dataclass(frozen=True, slots=True)
class ExecutionBudget:
    max_parallel_runs: int = 1
    max_runs: int = 500
    max_runtime_seconds: int = 3600
    max_retries_infra: int = 1
    artifact_retention: ArtifactRetention = "SUMMARY_PLUS_CERTIFICATES"

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_parallel_runs": self.max_parallel_runs,
            "max_runs": self.max_runs,
            "max_runtime_seconds": self.max_runtime_seconds,
            "max_retries_infra": self.max_retries_infra,
            "artifact_retention": self.artifact_retention,
        }


@dataclass(frozen=True, slots=True)
class CohortSpec:
    cohort_id: str
    label: str
    persona_presets: tuple[str, ...] = ()
    persona_distribution: dict[str, Any] | None = None
    sample_size: int = 1
    seed_start: int = 0
    seed_count: int = 1
    task_ids: tuple[str, ...] = ("default_task",)
    weight: float = 1.0
    conditions: tuple[str, ...] = (BASELINE_CONDITION,)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cohort_id": self.cohort_id,
            "label": self.label,
            "persona_presets": list(self.persona_presets),
            "persona_distribution": self.persona_distribution,
            "sample_size": self.sample_size,
            "seed_start": self.seed_start,
            "seed_count": self.seed_count,
            "task_ids": list(self.task_ids),
            "weight": self.weight,
            "conditions": list(self.conditions),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class PopulationSpec:
    population_id: str
    schema_version: int = SCHEMA_VERSION
    master_seed: int = 42
    tasks: tuple[str, ...] = ("default_task",)
    cohorts: tuple[CohortSpec, ...] = ()
    persona_source: PersonaSourceMode = "preset"
    runs_per_cell: int = 1
    execution_policy: ExecutionPolicy = "sequential"
    execution_budget: ExecutionBudget = field(default_factory=ExecutionBudget)
    aggregation_policy: dict[str, Any] = field(default_factory=dict)
    artifact_policy: dict[str, Any] = field(default_factory=dict)
    metrics_version: str = "metrics-v1"
    failure_taxonomy_version: str = "failures-v1"
    persona_schema_version: int = 1
    code_version: str = "local"
    metadata: dict[str, Any] = field(default_factory=dict)

    def spec_hash(self) -> str:
        blob = json.dumps(self._core_dict(), sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def _core_dict(self) -> dict[str, Any]:
        return {
            "population_id": self.population_id,
            "schema_version": self.schema_version,
            "master_seed": self.master_seed,
            "tasks": list(self.tasks),
            "cohorts": [c.to_dict() for c in self.cohorts],
            "persona_source": self.persona_source,
            "runs_per_cell": self.runs_per_cell,
            "execution_policy": self.execution_policy,
            "execution_budget": self.execution_budget.to_dict(),
            "aggregation_policy": dict(self.aggregation_policy),
            "artifact_policy": dict(self.artifact_policy),
            "metrics_version": self.metrics_version,
            "failure_taxonomy_version": self.failure_taxonomy_version,
            "persona_schema_version": self.persona_schema_version,
            "code_version": self.code_version,
            "metadata": dict(self.metadata),
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._core_dict(), "spec_hash": self.spec_hash()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PopulationSpec:
        cohorts = tuple(
            CohortSpec(
                cohort_id=str(c["cohort_id"]),
                label=str(c.get("label", c["cohort_id"])),
                persona_presets=tuple(c.get("persona_presets") or ()),
                persona_distribution=c.get("persona_distribution"),
                sample_size=int(c.get("sample_size", 1)),
                seed_start=int(c.get("seed_start", 0)),
                seed_count=int(c.get("seed_count", 1)),
                task_ids=tuple(c.get("task_ids") or data.get("tasks") or ("default_task",)),
                weight=float(c.get("weight", 1.0)),
                conditions=tuple(c.get("conditions") or (BASELINE_CONDITION,)),
                metadata=dict(c.get("metadata") or {}),
            )
            for c in data.get("cohorts") or []
        )
        budget_raw = data.get("execution_budget") or {}
        budget = ExecutionBudget(
            max_parallel_runs=int(budget_raw.get("max_parallel_runs", 1)),
            max_runs=int(budget_raw.get("max_runs", 500)),
            max_runtime_seconds=int(budget_raw.get("max_runtime_seconds", 3600)),
            max_retries_infra=int(budget_raw.get("max_retries_infra", 1)),
            artifact_retention=budget_raw.get("artifact_retention", "SUMMARY_PLUS_CERTIFICATES"),
        )
        return cls(
            population_id=str(data["population_id"]),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
            master_seed=int(data.get("master_seed", 42)),
            tasks=tuple(data.get("tasks") or ("default_task",)),
            cohorts=cohorts,
            persona_source=data.get("persona_source", "preset"),
            runs_per_cell=int(data.get("runs_per_cell", 1)),
            execution_policy=data.get("execution_policy", "sequential"),
            execution_budget=budget,
            aggregation_policy=dict(data.get("aggregation_policy") or {}),
            artifact_policy=dict(data.get("artifact_policy") or {}),
            metrics_version=str(data.get("metrics_version", "metrics-v1")),
            failure_taxonomy_version=str(data.get("failure_taxonomy_version", "failures-v1")),
            persona_schema_version=int(data.get("persona_schema_version", 1)),
            code_version=str(data.get("code_version", "local")),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass(frozen=True, slots=True)
class RunPlan:
    run_id: str
    population_id: str
    cohort_id: str
    task_id: str
    persona_id: str
    persona_config_hash: str
    seed: int
    condition_set_id: str
    sample_index: int
    config_versions: dict[str, str]
    artifact_path: str
    pair_id: str | None = None
    pair_role: str | None = None
    perturbation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "population_id": self.population_id,
            "cohort_id": self.cohort_id,
            "task_id": self.task_id,
            "persona_id": self.persona_id,
            "persona_config_hash": self.persona_config_hash,
            "seed": self.seed,
            "condition_set_id": self.condition_set_id,
            "sample_index": self.sample_index,
            "config_versions": dict(self.config_versions),
            "artifact_path": self.artifact_path,
            "pair_id": self.pair_id,
            "pair_role": self.pair_role,
            "perturbation_id": self.perturbation_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunPlan:
        return cls(
            run_id=str(data["run_id"]),
            population_id=str(data["population_id"]),
            cohort_id=str(data["cohort_id"]),
            task_id=str(data["task_id"]),
            persona_id=str(data["persona_id"]),
            persona_config_hash=str(data.get("persona_config_hash", "")),
            seed=int(data["seed"]),
            condition_set_id=str(data.get("condition_set_id", BASELINE_CONDITION)),
            sample_index=int(data.get("sample_index", 0)),
            config_versions=dict(data.get("config_versions") or {}),
            artifact_path=str(data.get("artifact_path", "")),
            pair_id=data.get("pair_id"),
            pair_role=data.get("pair_role"),
            perturbation_id=data.get("perturbation_id"),
        )


@dataclass
class RunExecutionRecord:
    plan: RunPlan
    status: RunStatus = RunStatus.PLANNED
    attempts: int = 0
    error: str | None = None
    summary_path: str | None = None
    trace_path: str | None = None
    certificate_ids: list[str] = field(default_factory=list)
    p6_summary: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan": self.plan.to_dict(),
            "status": self.status.value,
            "attempts": self.attempts,
            "error": self.error,
            "summary_path": self.summary_path,
            "trace_path": self.trace_path,
            "certificate_ids": list(self.certificate_ids),
            "p6_summary": self.p6_summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunExecutionRecord:
        return cls(
            plan=RunPlan.from_dict(data["plan"]),
            status=RunStatus(data.get("status", RunStatus.PLANNED.value)),
            attempts=int(data.get("attempts", 0)),
            error=data.get("error"),
            summary_path=data.get("summary_path"),
            trace_path=data.get("trace_path"),
            certificate_ids=list(data.get("certificate_ids") or []),
            p6_summary=data.get("p6_summary"),
        )
