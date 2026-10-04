"""Evaluation gates before any manual promote (S16)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.learning.models import LearningArtifact


@dataclass(frozen=True, slots=True)
class EvalGateResult:
    passed: bool
    reasons: tuple[str, ...]
    scores: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "reasons": list(self.reasons),
            "scores": dict(self.scores),
        }


def evaluate_artifact(
    artifact: LearningArtifact,
    *,
    baseline: LearningArtifact | None = None,
    min_coverage: float = 0.02,
    max_mean_weight: float = 0.95,
) -> EvalGateResult:
    """Fail closed on empty / runaway / missing disclaimer semantics."""
    reasons: list[str] = []
    scores = dict(artifact.metrics)
    coverage = float(artifact.metrics.get("coverage") or 0.0)
    mean_w = float(artifact.metrics.get("mean_weight") or 0.0)
    scores["coverage"] = coverage
    scores["mean_weight"] = mean_w

    if artifact.auto_deploy:
        reasons.append("auto_deploy must be false")
    if not artifact.weights:
        reasons.append("empty weights")
    if coverage < min_coverage:
        reasons.append(f"coverage below gate ({coverage:.4f} < {min_coverage})")
    if mean_w > max_mean_weight:
        reasons.append(f"mean_weight exceeds gate ({mean_w:.4f} > {max_mean_weight})")
    if baseline is not None:
        # Candidate should not collapse all baseline keys to zero.
        lost = sum(1 for k, v in baseline.weights.items() if v > 0.2 and artifact.weights.get(k, 0.0) < 0.01)
        scores["baseline_keys_lost"] = float(lost)
        if lost > max(3, len(baseline.weights) // 2):
            reasons.append("candidate drops too many baseline weights")

    return EvalGateResult(passed=not reasons, reasons=tuple(reasons), scores=scores)


def compare_phases(a: LearningArtifact, b: LearningArtifact) -> dict[str, Any]:
    """Side-by-side metrics for Phase A vs B (no automatic winner selection)."""
    return {
        "phase_a": {"artifact_id": a.artifact_id, "metrics": dict(a.metrics)},
        "phase_b": {"artifact_id": b.artifact_id, "metrics": dict(b.metrics)},
        "auto_select_winner": False,
        "note": "Operator must manually promote; comparison is informational only.",
    }
