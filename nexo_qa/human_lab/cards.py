"""Model Card and Data Card generation."""

from __future__ import annotations

from typing import Any

from nexo_qa.human_lab.models import CalibrationRecord, HumanCalibrationDataset


def build_model_card(record: CalibrationRecord, *, synthetic: bool = False) -> str:
    lines = [
        "# Model Card",
        "",
        f"**Calibration ID:** {record.calibration_id}",
        f"**Status:** {record.status}",
        "",
        "## Intended Use",
        "Compare NEXO simulation metrics with human behavioral data within declared CalibrationDomain.",
        "",
        "## Not Intended Use",
        "Clinical diagnosis, individual human prediction outside domain, or claims without holdout validation.",
        "",
        "## Limitations",
        "- EHFP is not a probability until HFP is validated",
        f"- HFP claim allowed: {record.hfp_claim_allowed}",
    ]
    if synthetic:
        lines.extend(["", "**SYNTHETIC_PIPELINE_TEST — NOT HUMAN VALIDATION**"])
    return "\n".join(lines)


def build_data_card(dataset: HumanCalibrationDataset) -> str:
    synthetic = any(r.synthetic for r in dataset.runs)
    lines = [
        "# Data Card",
        "",
        f"**Dataset ID:** {dataset.dataset_id}",
        f"**Human data status:** {dataset.human_data_status}",
        f"**Participants:** {dataset.participant_count}",
        f"**Runs:** {dataset.run_count}",
        f"**Manifest hash:** {dataset.manifest_hash()}",
        "",
        "## Privacy",
        "Participant IDs pseudonymized. Withdrawal/delete supported.",
    ]
    if synthetic:
        lines.extend(["", "**SYNTHETIC_PIPELINE_TEST — NOT HUMAN VALIDATION**"])
    return "\n".join(lines)


def model_card_manifest(record: CalibrationRecord, dataset: HumanCalibrationDataset) -> dict[str, Any]:
    return {
        "calibration_id": record.calibration_id,
        "dataset_id": dataset.dataset_id,
        "model_card_path": "MODEL_CARD.md",
        "data_card_path": "DATA_CARD.md",
        "hfp_claim_allowed": record.hfp_claim_allowed,
    }
