"""P9 Human Calibration Lab — core models."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

SCHEMA_VERSION = 1

HumanDataStatusValue = Literal[
    "NO_HUMAN_DATA",
    "PILOT",
    "CALIBRATION",
    "VALIDATION",
    "HOLDOUT_VALIDATED",
]

DomainScopeValue = Literal["CALIBRATED", "PARTIALLY_CALIBRATED", "OUT_OF_DOMAIN", "UNKNOWN"]

CalibrationStatus = Literal["EXPERIMENTAL", "VALIDATING", "VALIDATED_LIMITED", "VALIDATED", "RETIRED"]

HumanActionCategory = Literal[
    "ACTIVATE", "TYPE", "SELECT", "TOGGLE", "SCROLL", "BACK", "WAIT", "ABANDON", "OTHER"
]


class HumanDataStatus(str, Enum):
    NO_HUMAN_DATA = "NO_HUMAN_DATA"
    PILOT = "PILOT"
    CALIBRATION = "CALIBRATION"
    VALIDATION = "VALIDATION"
    HOLDOUT_VALIDATED = "HOLDOUT_VALIDATED"


@dataclass(frozen=True, slots=True)
class HumanTaskProtocol:
    task_id: str
    task_version: str
    environment_version: str
    goal_text: str
    condition: str = "BASELINE"
    time_limit_seconds: int | None = None
    success_predicate_ref: str = ""
    capture_policy: dict[str, Any] = field(default_factory=dict)
    exclusion_criteria: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_version": self.task_version,
            "environment_version": self.environment_version,
            "goal_text": self.goal_text,
            "condition": self.condition,
            "time_limit_seconds": self.time_limit_seconds,
            "success_predicate_ref": self.success_predicate_ref,
            "capture_policy": dict(self.capture_policy),
            "exclusion_criteria": list(self.exclusion_criteria),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HumanTaskProtocol:
        return cls(
            task_id=str(data["task_id"]),
            task_version=str(data.get("task_version", "1")),
            environment_version=str(data.get("environment_version", "web_lab_v1")),
            goal_text=str(data.get("goal_text", "")),
            condition=str(data.get("condition", "BASELINE")),
            time_limit_seconds=data.get("time_limit_seconds"),
            success_predicate_ref=str(data.get("success_predicate_ref", "")),
            capture_policy=dict(data.get("capture_policy") or {}),
            exclusion_criteria=tuple(data.get("exclusion_criteria") or ()),
        )


@dataclass(frozen=True, slots=True)
class HumanStudySpec:
    study_id: str
    schema_version: int = SCHEMA_VERSION
    title: str = ""
    tasks: tuple[HumanTaskProtocol, ...] = ()
    conditions: tuple[str, ...] = ("BASELINE",)
    assignment_strategy: str = "fixed"
    participant_target: int = 0
    consent_version: str = "consent_v1"
    retention_policy: str = "pseudonymous_90d"
    calibration_plan: dict[str, Any] = field(default_factory=dict)
    validation_plan: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "study_id": self.study_id,
            "schema_version": self.schema_version,
            "title": self.title,
            "tasks": [t.to_dict() for t in self.tasks],
            "conditions": list(self.conditions),
            "assignment_strategy": self.assignment_strategy,
            "participant_target": self.participant_target,
            "consent_version": self.consent_version,
            "retention_policy": self.retention_policy,
            "calibration_plan": dict(self.calibration_plan),
            "validation_plan": dict(self.validation_plan),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HumanStudySpec:
        study = data.get("study") or data
        tasks = tuple(HumanTaskProtocol.from_dict(t) for t in study.get("tasks") or [])
        return cls(
            study_id=str(study["study_id"]),
            schema_version=int(study.get("schema_version", SCHEMA_VERSION)),
            title=str(study.get("title", "")),
            tasks=tasks,
            conditions=tuple(study.get("conditions") or ("BASELINE",)),
            assignment_strategy=str(study.get("assignment_strategy", "fixed")),
            participant_target=int(study.get("participant_target", 0)),
            consent_version=str(study.get("consent_version", "consent_v1")),
            retention_policy=str(study.get("retention_policy", "pseudonymous_90d")),
            calibration_plan=dict(study.get("calibration_plan") or {}),
            validation_plan=dict(study.get("validation_plan") or {}),
            metadata=dict(study.get("metadata") or {}),
        )


@dataclass(frozen=True, slots=True)
class HumanInteractionEvent:
    participant_id: str
    human_run_id: str
    task_id: str
    event_id: str
    timestamp_ms: int
    event_type: str
    semantic_target: str = ""
    action_category: HumanActionCategory = "OTHER"
    page_state: str = ""
    outcome: str = ""
    progress_marker: str = ""
    error_marker: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "participant_id": self.participant_id,
            "human_run_id": self.human_run_id,
            "task_id": self.task_id,
            "event_id": self.event_id,
            "timestamp_ms": self.timestamp_ms,
            "event_type": self.event_type,
            "semantic_target": self.semantic_target,
            "action_category": self.action_category,
            "page_state": self.page_state,
            "outcome": self.outcome,
            "progress_marker": self.progress_marker,
            "error_marker": self.error_marker,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HumanInteractionEvent:
        return cls(
            participant_id=str(data["participant_id"]),
            human_run_id=str(data["human_run_id"]),
            task_id=str(data["task_id"]),
            event_id=str(data["event_id"]),
            timestamp_ms=int(data["timestamp_ms"]),
            event_type=str(data["event_type"]),
            semantic_target=str(data.get("semantic_target", "")),
            action_category=data.get("action_category", "OTHER"),
            page_state=str(data.get("page_state", "")),
            outcome=str(data.get("outcome", "")),
            progress_marker=str(data.get("progress_marker", "")),
            error_marker=str(data.get("error_marker", "")),
            metadata=dict(data.get("metadata") or {}),
        )


@dataclass
class HumanRunSummary:
    human_run_id: str
    participant_id: str
    task_id: str
    task_version: str
    environment_version: str
    condition: str
    completed: bool = False
    duration_ms: int = 0
    action_count: int = 0
    backtracks: int = 0
    repeated_actions: int = 0
    validation_errors: int = 0
    stagnation_events: int = 0
    recovery_episodes: int = 0
    abandoned: bool = False
    final_result: str = "UNKNOWN"
    perceived_difficulty: int | None = None
    perceived_frustration: int | None = None
    perceived_confidence: int | None = None
    synthetic: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "human_run_id": self.human_run_id,
            "participant_id": self.participant_id,
            "task_id": self.task_id,
            "task_version": self.task_version,
            "environment_version": self.environment_version,
            "condition": self.condition,
            "completed": self.completed,
            "duration_ms": self.duration_ms,
            "action_count": self.action_count,
            "backtracks": self.backtracks,
            "repeated_actions": self.repeated_actions,
            "validation_errors": self.validation_errors,
            "stagnation_events": self.stagnation_events,
            "recovery_episodes": self.recovery_episodes,
            "abandoned": self.abandoned,
            "final_result": self.final_result,
            "perceived_difficulty": self.perceived_difficulty,
            "perceived_frustration": self.perceived_frustration,
            "perceived_confidence": self.perceived_confidence,
            "synthetic": self.synthetic,
        }


@dataclass
class HumanCalibrationDataset:
    dataset_id: str
    schema_version: int = SCHEMA_VERSION
    study_id: str = ""
    task_versions: dict[str, str] = field(default_factory=dict)
    environment_versions: dict[str, str] = field(default_factory=dict)
    participant_count: int = 0
    run_count: int = 0
    conditions: tuple[str, ...] = ()
    capture_version: str = "capture_v1"
    annotation_version: str = "annotation_v0"
    human_data_status: HumanDataStatusValue = "NO_HUMAN_DATA"
    runs: list[HumanRunSummary] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def _manifest_payload(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "schema_version": self.schema_version,
            "study_id": self.study_id,
            "task_versions": dict(self.task_versions),
            "environment_versions": dict(self.environment_versions),
            "participant_count": self.participant_count,
            "run_count": self.run_count,
            "conditions": list(self.conditions),
            "capture_version": self.capture_version,
            "annotation_version": self.annotation_version,
            "human_data_status": self.human_data_status,
            "runs": [r.to_dict() for r in self.runs],
            "metadata": dict(self.metadata),
        }

    def manifest_hash(self) -> str:
        blob = json.dumps(self._manifest_payload(), sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self, *, include_runs: bool = True) -> dict[str, Any]:
        d = {
            "dataset_id": self.dataset_id,
            "schema_version": self.schema_version,
            "study_id": self.study_id,
            "task_versions": dict(self.task_versions),
            "environment_versions": dict(self.environment_versions),
            "participant_count": self.participant_count,
            "run_count": self.run_count,
            "conditions": list(self.conditions),
            "capture_version": self.capture_version,
            "annotation_version": self.annotation_version,
            "human_data_status": self.human_data_status,
            "metadata": dict(self.metadata),
        }
        if include_runs:
            d["runs"] = [r.to_dict() for r in self.runs]
            d["manifest_hash"] = self.manifest_hash()
        return d


@dataclass(frozen=True, slots=True)
class CalibrationDomain:
    domain_id: str
    task_families: tuple[str, ...] = ()
    ui_patterns: tuple[str, ...] = ()
    language: str = "en"
    viewport: str = "desktop"
    perturbations: tuple[str, ...] = ()
    participant_scope: str = "adults_general"
    excluded_domains: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "task_families": list(self.task_families),
            "ui_patterns": list(self.ui_patterns),
            "language": self.language,
            "viewport": self.viewport,
            "perturbations": list(self.perturbations),
            "participant_scope": self.participant_scope,
            "excluded_domains": list(self.excluded_domains),
        }

    def scope_for(self, *, task_id: str, condition: str) -> DomainScopeValue:
        if task_id and self.task_families and task_id not in self.task_families:
            return "OUT_OF_DOMAIN"
        if condition != "BASELINE" and self.perturbations and condition not in self.perturbations:
            return "PARTIALLY_CALIBRATED"
        if task_id in self.task_families:
            return "CALIBRATED"
        return "UNKNOWN"


@dataclass
class CalibrationRecord:
    calibration_id: str
    status: CalibrationStatus = "EXPERIMENTAL"
    dataset_id: str = ""
    domain_id: str = ""
    metrics_version: str = "metrics-v1"
    taxonomy_version: str = "failures-v1"
    persona_version: int = 1
    model_versions: dict[str, str] = field(default_factory=dict)
    validation_results: dict[str, Any] = field(default_factory=dict)
    hfp_claim_allowed: bool = False
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "calibration_id": self.calibration_id,
            "status": self.status,
            "dataset_id": self.dataset_id,
            "domain_id": self.domain_id,
            "metrics_version": self.metrics_version,
            "taxonomy_version": self.taxonomy_version,
            "persona_version": self.persona_version,
            "model_versions": dict(self.model_versions),
            "validation_results": dict(self.validation_results),
            "hfp_claim_allowed": self.hfp_claim_allowed,
            "created_at": self.created_at,
        }
