"""Distillation sandbox — Phase A/B toy weight updates from experience claims.

Not a neural trainer. Not proof of collective intelligence.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from services.learning.models import LearningArtifact, LearningPhase, new_artifact_id


def distill_from_claims(
    *,
    phase: LearningPhase,
    claims: Iterable[Mapping[str, Any]],
    base_weights: Mapping[str, float] | None = None,
    parent_id: str | None = None,
    experience_ids: list[str] | None = None,
) -> LearningArtifact:
    """Build a sandbox artifact by aggregating claim tokens into bounded weights."""
    weights = {str(k): float(v) for k, v in dict(base_weights or {}).items()}
    n = 0
    for claim in claims:
        text = str(claim.get("claim") or claim.get("content") or "").strip().lower()
        if not text:
            continue
        conf = float(claim.get("confidence") if claim.get("confidence") is not None else 0.5)
        conf = max(0.0, min(1.0, conf))
        # Tokenize simply; phase B learns slightly more aggressively (still sandbox-only).
        rate = 0.05 if phase is LearningPhase.A else 0.08
        for token in text.replace(".", " ").replace(",", " ").split():
            if len(token) < 3:
                continue
            prev = weights.get(token, 0.0)
            weights[token] = max(0.0, min(1.0, prev + rate * conf))
            n += 1
    coverage = float(min(1.0, n / 50.0)) if n else 0.0
    mean_w = (sum(weights.values()) / len(weights)) if weights else 0.0
    return LearningArtifact(
        artifact_id=new_artifact_id(phase),
        phase=phase,
        weights=weights,
        metrics={
            "claim_tokens_touched": float(n),
            "weight_count": float(len(weights)),
            "mean_weight": float(mean_w),
            "coverage": coverage,
        },
        parent_id=parent_id,
        source_experience_ids=list(experience_ids or []),
    )
