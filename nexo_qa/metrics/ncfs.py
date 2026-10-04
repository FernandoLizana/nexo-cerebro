"""NCFS — NEXO Cognitive Friction Score v1."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nexo_qa.failures.taxonomy import CognitiveFailure, FailureFamily
from nexo_qa.metrics.models import MetricResult

NCFS_VERSION = "ncfs_v1"

DEFAULT_WEIGHTS = {
    "perceptual": 0.15,
    "attention": 0.18,
    "semantic": 0.12,
    "memory": 0.12,
    "decision": 0.13,
    "navigation": 0.15,
    "recovery": 0.15,
}


@dataclass
class NCFSResult:
    version: str = NCFS_VERSION
    value: float | None = None
    components: dict[str, float | None] = field(default_factory=dict)
    coverage: float = 0.0
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    disclaimer: str = "simulation-derived; not human-calibrated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "value": None if self.value is None else round(self.value, 2),
            "components": {k: None if v is None else round(v, 2) for k, v in self.components.items()},
            "coverage": round(self.coverage, 4),
            "weights": dict(self.weights),
            "disclaimer": self.disclaimer,
        }


def _family_friction(failures: list[CognitiveFailure], family: FailureFamily) -> float | None:
    matched = [f for f in failures if f.family == family]
    if not matched:
        return 0.0
    sev_map = {"INFO": 0.1, "LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.75, "CRITICAL": 1.0}
    return min(1.0, sum(sev_map.get(f.severity, 0.3) for f in matched) / max(1, len(matched)))


def compute_ncfs(
    failures: list[CognitiveFailure],
    *,
    weights: dict[str, float] | None = None,
) -> NCFSResult:
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)
    if not failures:
        empty_components = {k: None for k in ("perceptual", "attention", "semantic", "memory", "decision", "navigation", "recovery")}
        return NCFSResult(value=None, components=empty_components, coverage=0.0)
    components: dict[str, float | None] = {
        "perceptual": _family_friction(failures, FailureFamily.PERCEPTION),
        "attention": _family_friction(failures, FailureFamily.ATTENTION),
        "semantic": _family_friction(failures, FailureFamily.SEMANTIC),
        "memory": _family_friction(failures, FailureFamily.MEMORY),
        "decision": _family_friction(failures, FailureFamily.DECISION),
        "navigation": _family_friction(failures, FailureFamily.NAVIGATION),
        "recovery": _family_friction(failures, FailureFamily.RECOVERY),
    }
    available = [k for k, v in components.items() if v is not None]
    if not available:
        return NCFSResult(value=None, components=components, coverage=0.0)
    weighted = sum(float(components[k]) * w[k] for k in available)
    weight_sum = sum(w[k] for k in available)
    normalized = (weighted / weight_sum) * 100.0 if weight_sum else None
    return NCFSResult(
        value=normalized,
        components=components,
        coverage=len(available) / len(components),
    )


def ncfs_metric_result(ncfs: NCFSResult) -> MetricResult:
    return MetricResult(
        metric_id="ncfs_v1",
        value=ncfs.value,
        status="AVAILABLE" if ncfs.value is not None else "NOT_AVAILABLE",
        coverage=ncfs.coverage,
        version=NCFS_VERSION,
        metadata=ncfs.to_dict(),
    )
