"""P8 perturbation and chaos models."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

SCHEMA_VERSION = 1
BASELINE_CONDITION = "BASELINE"

PerturbationType = Literal[
    "INTERRUPTION",
    "LATENCY",
    "TRANSIENT_ERROR",
    "SESSION_EXPIRY",
    "VISUAL_CHANGE",
    "MODAL_DISTRACTION",
    "CONTENT_SHIFT",
    "FEEDBACK_DELAY",
    "CONTROL_DISABLE",
    "NETWORK_LIKE_FAILURE",
]

TriggerKind = Literal[
    "AT_TICK",
    "AFTER_ACTION",
    "ON_PAGE",
    "ON_GOAL_PROGRESS",
    "AFTER_DURATION",
    "PROBABILISTIC_SEEDED",
]

PairRole = Literal["baseline", "perturbed"]
PairValidity = Literal["VALID", "INVALID_PAIR", "INCOMPATIBLE_PAIR"]


class PerturbationEventType(str, Enum):
    SCHEDULED = "PERTURBATION_SCHEDULED"
    STARTED = "PERTURBATION_STARTED"
    UPDATED = "PERTURBATION_UPDATED"
    ENDED = "PERTURBATION_ENDED"
    INJECTION_FAILURE = "PERTURBATION_INJECTION_FAILURE"


@dataclass(frozen=True, slots=True)
class TriggerSpec:
    kind: TriggerKind = "AT_TICK"
    at_tick: int | None = None
    after_action_count: int | None = None
    after_duration_ticks: int | None = None
    on_page: str | None = None
    probability: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "at_tick": self.at_tick,
            "after_action_count": self.after_action_count,
            "after_duration_ticks": self.after_duration_ticks,
            "on_page": self.on_page,
            "probability": self.probability,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> TriggerSpec:
        data = data or {}
        return cls(
            kind=data.get("kind", "AT_TICK"),
            at_tick=data.get("at_tick"),
            after_action_count=data.get("after_action_count"),
            after_duration_ticks=data.get("after_duration_ticks"),
            on_page=data.get("on_page"),
            probability=data.get("probability"),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass(frozen=True, slots=True)
class PerturbationSpec:
    perturbation_id: str
    type: PerturbationType
    trigger: TriggerSpec = field(default_factory=TriggerSpec)
    intensity: float = 1.0
    duration_ticks: int = 3
    target_scope: str = "environment"
    parameters: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None
    repeat_policy: str = "once"
    schema_version: int = SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def spec_hash(self) -> str:
        blob = json.dumps(self.to_dict(include_hash=False), sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()[:12]

    def to_dict(self, *, include_hash: bool = True) -> dict[str, Any]:
        d = {
            "perturbation_id": self.perturbation_id,
            "schema_version": self.schema_version,
            "type": self.type,
            "trigger": self.trigger.to_dict(),
            "intensity": self.intensity,
            "duration_ticks": self.duration_ticks,
            "target_scope": self.target_scope,
            "parameters": dict(self.parameters),
            "seed": self.seed,
            "repeat_policy": self.repeat_policy,
            "metadata": dict(self.metadata),
        }
        if include_hash:
            d["spec_hash"] = self.spec_hash()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PerturbationSpec:
        return cls(
            perturbation_id=str(data["perturbation_id"]),
            type=data["type"],
            trigger=TriggerSpec.from_dict(data.get("trigger")),
            intensity=float(data.get("intensity", 1.0)),
            duration_ticks=int(data.get("duration_ticks", 3)),
            target_scope=str(data.get("target_scope", "environment")),
            parameters=dict(data.get("parameters") or {}),
            seed=data.get("seed"),
            repeat_policy=str(data.get("repeat_policy", "once")),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass(frozen=True, slots=True)
class ChaosSpec:
    chaos_id: str
    schema_version: int = SCHEMA_VERSION
    paired: bool = True
    master_seed: int = 42
    task_id: str = "default_task"
    persona_preset: str = "baseline"
    perturbations: tuple[PerturbationSpec, ...] = ()
    cohort_id: str = "baseline"
    metrics_version: str = "metrics-v1"
    failure_taxonomy_version: str = "failures-v1"
    code_version: str = "local"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chaos_id": self.chaos_id,
            "schema_version": self.schema_version,
            "paired": self.paired,
            "master_seed": self.master_seed,
            "task_id": self.task_id,
            "persona_preset": self.persona_preset,
            "perturbations": [p.to_dict() for p in self.perturbations],
            "cohort_id": self.cohort_id,
            "metrics_version": self.metrics_version,
            "failure_taxonomy_version": self.failure_taxonomy_version,
            "code_version": self.code_version,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChaosSpec:
        raw = data.get("chaos") or data
        perturbations = tuple(
            PerturbationSpec.from_dict(p) for p in raw.get("perturbations") or []
        )
        return cls(
            chaos_id=str(raw.get("chaos_id") or raw.get("id") or "chaos"),
            schema_version=int(raw.get("schema_version", SCHEMA_VERSION)),
            paired=bool(raw.get("paired", True)),
            master_seed=int(raw.get("master_seed", 42)),
            task_id=str(raw.get("task_id", "default_task")),
            persona_preset=str(raw.get("persona_preset", "baseline")),
            perturbations=perturbations,
            cohort_id=str(raw.get("cohort_id", "baseline")),
            metrics_version=str(raw.get("metrics_version", "metrics-v1")),
            failure_taxonomy_version=str(raw.get("failure_taxonomy_version", "failures-v1")),
            code_version=str(raw.get("code_version", "local")),
            metadata=dict(raw.get("metadata") or {}),
        )


@dataclass(frozen=True, slots=True)
class ChaosPairPlan:
    pair_id: str
    perturbation: PerturbationSpec
    baseline_run_id: str
    perturbed_run_id: str
    task_id: str
    persona_id: str
    seed: int
    condition_baseline: str = BASELINE_CONDITION
    condition_perturbed: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair_id": self.pair_id,
            "perturbation": self.perturbation.to_dict(),
            "baseline_run_id": self.baseline_run_id,
            "perturbed_run_id": self.perturbed_run_id,
            "task_id": self.task_id,
            "persona_id": self.persona_id,
            "seed": self.seed,
            "condition_baseline": self.condition_baseline,
            "condition_perturbed": self.condition_perturbed,
        }


@dataclass
class ChaosPlan:
    chaos_id: str
    spec_hash: str
    pairs: tuple[ChaosPairPlan, ...]
    runs: tuple[Any, ...]  # RunPlan from population

    def to_dict(self) -> dict[str, Any]:
        return {
            "chaos_id": self.chaos_id,
            "spec_hash": self.spec_hash,
            "pairs": [p.to_dict() for p in self.pairs],
            "runs": [r.to_dict() for r in self.runs],
            "planned_pairs": len(self.pairs),
            "planned_runs": len(self.runs),
        }

    def write_json(self, path: Any) -> None:
        from pathlib import Path

        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")


@dataclass
class PairedChaosDelta:
    pair_id: str
    validity: PairValidity
    baseline_run_id: str
    perturbed_run_id: str
    metric_deltas: dict[str, float | None] = field(default_factory=dict)
    failure_deltas: dict[str, int] = field(default_factory=dict)
    status_change: str | None = None
    recovery_delta: float | None = None
    interruption_recovery_ticks: int | None = None
    artifact_refs: dict[str, str] = field(default_factory=dict)
    invalid_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair_id": self.pair_id,
            "validity": self.validity,
            "baseline_run_id": self.baseline_run_id,
            "perturbed_run_id": self.perturbed_run_id,
            "metric_deltas": self.metric_deltas,
            "failure_deltas": self.failure_deltas,
            "status_change": self.status_change,
            "recovery_delta": self.recovery_delta,
            "interruption_recovery_ticks": self.interruption_recovery_ticks,
            "artifact_refs": dict(self.artifact_refs),
            "invalid_reason": self.invalid_reason,
        }


@dataclass
class InjectionCoverage:
    planned: int = 0
    injected: int = 0
    missed: int = 0
    failures: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "planned": self.planned,
            "successfully_injected": self.injected,
            "missed": self.missed,
            "injection_failures": self.failures,
        }
