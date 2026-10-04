"""NCFS validation pipeline."""

from __future__ import annotations

from typing import Any

from nexo_qa.human_lab.statistics import bootstrap_ci, pearson_correlation, spearman_correlation


def validate_ncfs_against_human(
    human_summaries: list[dict[str, Any]],
    nexo_summaries: list[dict[str, Any]],
    *,
    synthetic: bool = False,
) -> dict[str, Any]:
    n = min(len(human_summaries), len(nexo_summaries))
    if n < 3:
        return {
            "status": "INSUFFICIENT_SAMPLE",
            "n": n,
            "ncfs_version": "ncfs_v1",
            "recalibration_required": None,
            "synthetic": synthetic,
        }
    human_proxy = [
        float(s.get("validation_errors", 0)) + float(s.get("repeated_actions", 0))
        for s in human_summaries[:n]
    ]
    nexo_ncfs = [float((s.get("ncfs") or {}).get("value", 0)) for s in nexo_summaries[:n]]
    return {
        "status": "PIPELINE_READY" if synthetic else "AWAITING_HUMAN_DATA",
        "n": n,
        "ncfs_version": "ncfs_v1",
        "pearson_vs_human_friction_proxy": pearson_correlation(nexo_ncfs, human_proxy),
        "spearman_vs_action_count": spearman_correlation(
            nexo_ncfs, [float(s.get("action_count", 0)) for s in human_summaries[:n]]
        ),
        "ci": bootstrap_ci(nexo_ncfs, human_proxy),
        "recalibration_required": False,
        "note": "ncfs_v1 unchanged — new weights require ncfs_v2",
        "synthetic": synthetic,
        "disclaimer": "SYNTHETIC_PIPELINE_TEST — NOT HUMAN VALIDATION" if synthetic else "",
    }
