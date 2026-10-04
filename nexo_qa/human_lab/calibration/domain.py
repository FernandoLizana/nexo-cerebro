"""Calibration domain and OOD policy."""

from __future__ import annotations

from typing import Any

from nexo_qa.human_lab.models import CalibrationDomain, DomainScopeValue


def evaluate_domain_scope(
    domain: CalibrationDomain,
    *,
    task_id: str,
    condition: str,
    language: str = "en",
    viewport: str = "desktop",
) -> DomainScopeValue:
    if language != domain.language:
        return "OUT_OF_DOMAIN"
    if viewport != domain.viewport:
        return "PARTIALLY_CALIBRATED"
    return domain.scope_for(task_id=task_id, condition=condition)


def block_hfp_claim(scope: DomainScopeValue, *, calibration_validated: bool) -> tuple[bool, str]:
    if not calibration_validated:
        return False, "calibration not validated"
    if scope == "OUT_OF_DOMAIN":
        return False, "OUT_OF_DOMAIN"
    if scope in ("UNKNOWN", "PARTIALLY_CALIBRATED"):
        return False, f"scope={scope}"
    return True, "allowed in CALIBRATED domain"


def ood_policy_manifest() -> dict[str, Any]:
    return {
        "out_of_domain_behavior": "HFP=NOT_AVAILABLE",
        "partially_calibrated_behavior": "HFP=NOT_AVAILABLE",
        "unknown_behavior": "HFP=NOT_AVAILABLE",
        "requires": ["calibration_id", "domain_id", "model_version", "holdout_evaluation"],
    }
