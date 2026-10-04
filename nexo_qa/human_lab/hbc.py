"""HBC — Human Behavioral Correlation components."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nexo_qa.human_lab.alignment import AlignmentResult, BehavioralAlignmentAnalyzer
from nexo_qa.human_lab.statistics import bootstrap_ci, pearson_correlation


@dataclass
class HBCResult:
    hbc_outcome: float | None = None
    hbc_path: float | None = None
    hbc_failure: float | None = None
    hbc_recovery: float | None = None
    hbc_perturbation: float | None = None
    composite: float | None = None
    composite_weights: dict[str, float] = field(default_factory=dict)
    ci: dict[str, Any] = field(default_factory=dict)
    n: int = 0
    synthetic: bool = False
    disclaimer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "hbc_outcome": self.hbc_outcome,
            "hbc_path": self.hbc_path,
            "hbc_failure": self.hbc_failure,
            "hbc_recovery": self.hbc_recovery,
            "hbc_perturbation": self.hbc_perturbation,
            "composite": self.composite,
            "composite_weights": dict(self.composite_weights),
            "ci": dict(self.ci),
            "n": self.n,
            "synthetic": self.synthetic,
            "disclaimer": self.disclaimer,
        }


def compute_hbc(
    alignment: AlignmentResult,
    *,
    synthetic: bool = False,
    human_action_counts: list[float] | None = None,
    nexo_action_counts: list[float] | None = None,
) -> HBCResult:
    weights = {
        "outcome": 0.25,
        "path": 0.25,
        "failure": 0.2,
        "recovery": 0.15,
        "perturbation": 0.15,
    }
    components = {
        "outcome": alignment.outcome_alignment,
        "path": alignment.path_alignment,
        "failure": alignment.failure_alignment,
        "recovery": alignment.recovery_alignment,
        "perturbation": alignment.perturbation_response_alignment,
    }
    available = {k: v for k, v in components.items() if v is not None}
    composite = None
    if available:
        w_sum = sum(weights[k] for k in available)
        composite = round(sum(available[k] * weights[k] for k in available) / w_sum, 4)

    ci = {}
    if human_action_counts and nexo_action_counts:
        ci = bootstrap_ci(human_action_counts, nexo_action_counts)

    disclaimer = "SYNTHETIC_PIPELINE_TEST — NOT HUMAN VALIDATION" if synthetic else "requires real human data for validation claims"

    return HBCResult(
        hbc_outcome=alignment.outcome_alignment,
        hbc_path=alignment.path_alignment,
        hbc_failure=alignment.failure_alignment,
        hbc_recovery=alignment.recovery_alignment,
        hbc_perturbation=alignment.perturbation_response_alignment,
        composite=composite,
        composite_weights=weights,
        ci=ci,
        n=alignment.n_pairs,
        synthetic=synthetic,
        disclaimer=disclaimer,
    )


def compute_hbc_from_summaries(
    human_summaries: list[dict[str, Any]],
    nexo_summaries: list[dict[str, Any]],
    *,
    synthetic: bool = False,
) -> HBCResult:
    alignment = BehavioralAlignmentAnalyzer().analyze(
        human_summaries=human_summaries,
        nexo_summaries=nexo_summaries,
    )
    return compute_hbc(
        alignment,
        synthetic=synthetic,
        human_action_counts=[float(s.get("action_count", 0)) for s in human_summaries],
        nexo_action_counts=[float(s.get("action_count", 0)) for s in nexo_summaries],
    )
