"""Metric models and status."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

MetricStatus = Literal["AVAILABLE", "PARTIAL", "NOT_AVAILABLE", "INVALID"]


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    metric_id: str
    name: str
    version: str
    scope: str
    range_min: float
    range_max: float
    units: str
    formula: str
    required_inputs: tuple[str, ...]
    interpretation: str
    limitations: str
    calibration: str = "not human-calibrated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "version": self.version,
            "scope": self.scope,
            "range": [self.range_min, self.range_max],
            "units": self.units,
            "formula": self.formula,
            "required_inputs": list(self.required_inputs),
            "interpretation": self.interpretation,
            "limitations": self.limitations,
            "calibration": self.calibration,
        }


@dataclass(frozen=True, slots=True)
class MetricResult:
    metric_id: str
    value: float | None
    status: MetricStatus
    coverage: float
    evidence_refs: tuple[str, ...] = ()
    version: str = "metrics-v1"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "value": None if self.value is None else round(float(self.value), 4),
            "status": self.status,
            "coverage": round(self.coverage, 4),
            "evidence_refs": list(self.evidence_refs),
            "version": self.version,
            "metadata": dict(self.metadata),
        }
