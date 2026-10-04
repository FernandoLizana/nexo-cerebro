"""EHFP → HFP calibration with claim safety."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nexo_qa.human_lab.calibration.domain import block_hfp_claim
from nexo_qa.human_lab.models import DomainScopeValue, HumanDataStatus
from nexo_qa.human_lab.statistics import brier_score, expected_calibration_error


@dataclass
class HFPResult:
    value: float | None
    available: bool
    calibration_id: str | None
    domain_id: str | None
    model_version: str | None
    reason: str
    is_probability: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "available": self.available,
            "calibration_id": self.calibration_id,
            "domain_id": self.domain_id,
            "model_version": self.model_version,
            "reason": self.reason,
            "is_probability": self.is_probability,
        }


def hfp_claim_allowed(
    *,
    human_data_status: str,
    calibration_status: str,
    domain_scope: DomainScopeValue,
    holdout_evaluated: bool,
) -> tuple[bool, str]:
    if human_data_status in (HumanDataStatus.NO_HUMAN_DATA.value, "NO_HUMAN_DATA"):
        return False, "NO_HUMAN_DATA"
    if calibration_status not in ("VALIDATED", "VALIDATED_LIMITED", "HOLDOUT_VALIDATED"):
        return False, f"calibration_status={calibration_status}"
    if not holdout_evaluated:
        return False, "holdout evaluation required"
    allowed, reason = block_hfp_claim(domain_scope, calibration_validated=True)
    return allowed, reason


def calibrate_ehfp_to_hfp(
    ehfp_values: list[float],
    human_failures: list[int],
    *,
    calibration_id: str,
    domain_id: str,
    model_version: str = "hfp_v0",
    human_data_status: str = "NO_HUMAN_DATA",
    calibration_status: str = "EXPERIMENTAL",
    domain_scope: DomainScopeValue = "UNKNOWN",
    holdout_evaluated: bool = False,
) -> dict[str, Any]:
    allowed, reason = hfp_claim_allowed(
        human_data_status=human_data_status,
        calibration_status=calibration_status,
        domain_scope=domain_scope,
        holdout_evaluated=holdout_evaluated,
    )
    brier = brier_score(ehfp_values, human_failures) if ehfp_values else None
    ece = expected_calibration_error(ehfp_values, human_failures) if ehfp_values else None
    hfp = HFPResult(
        value=None,
        available=allowed,
        calibration_id=calibration_id if allowed else None,
        domain_id=domain_id if allowed else None,
        model_version=model_version if allowed else None,
        reason=reason if not allowed else "calibrated",
        is_probability=allowed,
    )
    return {
        "ehfp_version": "ehfp_v1",
        "hfp": hfp.to_dict(),
        "hfp_claim_allowed": allowed,
        "brier_score": brier,
        "ece": ece,
        "calibration_curve": _calibration_curve(ehfp_values, human_failures) if ehfp_values else [],
        "disclaimer": "EHFP remains proxy until validated HFP",
    }


def _calibration_curve(probs: list[float], outcomes: list[int], bins: int = 5) -> list[dict[str, Any]]:
    bucket: dict[int, list[tuple[float, int]]] = {i: [] for i in range(bins)}
    for p, o in zip(probs, outcomes):
        bucket[min(bins - 1, int(p * bins))].append((p, o))
    curve = []
    for i, items in bucket.items():
        if not items:
            continue
        curve.append(
            {
                "bin": i,
                "mean_predicted": round(sum(x[0] for x in items) / len(items), 4),
                "mean_observed": round(sum(x[1] for x in items) / len(items), 4),
                "n": len(items),
            }
        )
    return curve
