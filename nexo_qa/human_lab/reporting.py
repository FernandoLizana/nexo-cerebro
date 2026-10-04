"""Calibration reporting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_calibration_report(
    *,
    human_data_status: str,
    study_id: str,
    dataset_id: str,
    calibration_result: dict[str, Any],
    hfp_claim_allowed: bool,
    synthetic: bool = False,
) -> dict[str, Any]:
    return {
        "report_type": "calibration_report",
        "schema_version": 1,
        "executive_summary": {
            "human_data_status": human_data_status,
            "study_id": study_id,
            "dataset_id": dataset_id,
            "hfp_claim_allowed": hfp_claim_allowed,
            "verdict": "CONDITIONAL PASS — HUMAN DATA REQUIRED" if human_data_status == "NO_HUMAN_DATA" else "PIPELINE_READY",
        },
        "human_data_status": human_data_status,
        "behavioral_alignment": calibration_result.get("hbc"),
        "hbc": calibration_result.get("hbc"),
        "ncfs_validation": calibration_result.get("ncfs_validation"),
        "crs_validation": calibration_result.get("crs_validation"),
        "ehfp_hfp_calibration": calibration_result.get("ehfp_hfp"),
        "final_verdict": "CONDITIONAL PASS — HUMAN DATA REQUIRED" if human_data_status == "NO_HUMAN_DATA" else "AWAITING_VALIDATION",
        "disclaimer_en": "Results are from NEXO Cognitive QA calibration pipeline. Human validation requires real participant data.",
        "pipeline_label": "SYNTHETIC_PIPELINE_TEST — NOT HUMAN VALIDATION" if synthetic else None,
    }


def write_calibration_report_json(path: Path | str, report: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_calibration_report_markdown(report: dict[str, Any]) -> str:
    summary = report.get("executive_summary") or {}
    lines = [
        "# Calibration Report",
        "",
        f"- Human data status: {summary.get('human_data_status')}",
        f"- HFP claim allowed: {summary.get('hfp_claim_allowed')}",
        f"- Verdict: {summary.get('verdict')}",
        "",
        report.get("disclaimer_en", ""),
    ]
    if report.get("pipeline_label"):
        lines.extend(["", report["pipeline_label"]])
    return "\n".join(lines)
