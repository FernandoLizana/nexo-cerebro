"""Calibration engine — fit, validate, register."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from nexo_qa.human_lab.calibration.crs_validation import validate_crs_against_human
from nexo_qa.human_lab.calibration.domain import evaluate_domain_scope
from nexo_qa.human_lab.calibration.ehfp_hfp import calibrate_ehfp_to_hfp, hfp_claim_allowed
from nexo_qa.human_lab.calibration.ncfs_validation import validate_ncfs_against_human
from nexo_qa.human_lab.calibration.registry import CalibrationRegistry
from nexo_qa.human_lab.hbc import compute_hbc_from_summaries
from nexo_qa.human_lab.models import CalibrationDomain, CalibrationRecord, HumanCalibrationDataset


@dataclass
class CalibrationEngine:
    registry: CalibrationRegistry = field(default_factory=CalibrationRegistry)

    def fit_and_validate(
        self,
        *,
        dataset: HumanCalibrationDataset,
        domain: CalibrationDomain,
        human_summaries: list[dict[str, Any]],
        nexo_summaries: list[dict[str, Any]],
        synthetic: bool = False,
    ) -> dict[str, Any]:
        calibration_id = f"cal-{dataset.dataset_id}"
        hbc = compute_hbc_from_summaries(human_summaries, nexo_summaries, synthetic=synthetic)
        ncfs = validate_ncfs_against_human(human_summaries, nexo_summaries, synthetic=synthetic)
        crs = validate_crs_against_human(human_summaries, nexo_summaries, synthetic=synthetic)
        ehfp_vals = [float((s.get("ehfp") or {}).get("value", 0.5)) for s in nexo_summaries]
        human_fail = [0 if s.get("completed") else 1 for s in human_summaries]
        scope = evaluate_domain_scope(domain, task_id=human_summaries[0].get("task_id", ""), condition="BASELINE") if human_summaries else "UNKNOWN"
        holdout = bool(dataset.metadata.get("holdout_evaluated"))
        hfp = calibrate_ehfp_to_hfp(
            ehfp_vals,
            human_fail,
            calibration_id=calibration_id,
            domain_id=domain.domain_id,
            human_data_status=dataset.human_data_status,
            calibration_status="EXPERIMENTAL" if synthetic else "VALIDATING",
            domain_scope=scope,
            holdout_evaluated=holdout,
        )
        allowed, _ = hfp_claim_allowed(
            human_data_status=dataset.human_data_status,
            calibration_status="EXPERIMENTAL",
            domain_scope=scope,
            holdout_evaluated=holdout,
        )
        record = CalibrationRecord(
            calibration_id=calibration_id,
            status="EXPERIMENTAL" if synthetic else "VALIDATING",
            dataset_id=dataset.dataset_id,
            domain_id=domain.domain_id,
            validation_results={"hbc": hbc.to_dict(), "ncfs": ncfs, "crs": crs, "hfp": hfp},
            hfp_claim_allowed=allowed,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.registry.register(record)
        return {
            "calibration_id": calibration_id,
            "hbc": hbc.to_dict(),
            "ncfs_validation": ncfs,
            "crs_validation": crs,
            "ehfp_hfp": hfp,
            "hfp_claim_allowed": allowed,
            "synthetic": synthetic,
        }
