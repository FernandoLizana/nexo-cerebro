"""Evaluation harness for federated research rounds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class EvalReport:
    passed: bool
    scores: dict[str, float]
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "scores": dict(self.scores), "notes": list(self.notes)}


def evaluate_global_weights(
    weights: Mapping[str, float],
    *,
    holdout_claims: list[Mapping[str, Any]] | None = None,
    max_mean_abs: float = 0.9,
) -> EvalReport:
    notes: list[str] = []
    values = [abs(float(v)) for v in weights.values()]
    mean_abs = (sum(values) / len(values)) if values else 0.0
    scores = {
        "weight_count": float(len(weights)),
        "mean_abs": float(mean_abs),
    }
    if not weights:
        notes.append("empty global weights")
    if mean_abs > max_mean_abs:
        notes.append(f"mean_abs too high ({mean_abs:.4f})")

    # Simple holdout overlap score: fraction of claim tokens present with weight > 0
    if holdout_claims:
        tokens: set[str] = set()
        for claim in holdout_claims:
            text = str(claim.get("claim") or "").lower()
            tokens.update(t for t in text.split() if len(t) >= 3)
        if tokens:
            hit = sum(1 for t in tokens if float(weights.get(t, 0.0)) > 0.0)
            overlap = hit / len(tokens)
            scores["holdout_overlap"] = float(overlap)
            if overlap < 0.05:
                notes.append("holdout overlap below research gate")
        else:
            scores["holdout_overlap"] = 0.0

    return EvalReport(passed=not notes, scores=scores, notes=tuple(notes))
