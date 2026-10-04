"""Failure severity model — versioned, deterministic."""

from __future__ import annotations

from dataclasses import dataclass

SEVERITY_VERSION = "severity-v1"

SEVERITY_ORDER = ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")


@dataclass(frozen=True, slots=True)
class SeverityResult:
    severity: str
    severity_score: float
    factors: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "severity_score": round(self.severity_score, 4),
            "factors": {k: round(v, 4) for k, v in self.factors.items()},
            "version": SEVERITY_VERSION,
        }


def compute_severity(
    *,
    goal_impact: float = 0.0,
    recovery_cost: float = 0.0,
    risk_weight: float = 0.0,
    persistence: float = 0.0,
    terminal_failure: bool = False,
) -> SeverityResult:
    """Simple versioned severity formula."""
    terminal_w = 0.35 if terminal_failure else 0.0
    score = goal_impact * 0.35 + recovery_cost * 0.2 + risk_weight * 0.2 + persistence * 0.15 + terminal_w
    score = max(0.0, min(1.0, score))
    if score >= 0.85:
        level = "CRITICAL"
    elif score >= 0.65:
        level = "HIGH"
    elif score >= 0.45:
        level = "MEDIUM"
    elif score >= 0.25:
        level = "LOW"
    else:
        level = "INFO"
    return SeverityResult(
        severity=level,
        severity_score=score,
        factors={
            "goal_impact": goal_impact,
            "recovery_cost": recovery_cost,
            "risk_weight": risk_weight,
            "persistence": persistence,
            "terminal_failure_weight": terminal_w,
        },
    )
