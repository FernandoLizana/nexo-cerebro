"""CRS validation pipeline."""

from __future__ import annotations

from typing import Any

from nexo_qa.human_lab.statistics import bootstrap_ci, pearson_correlation


def validate_crs_against_human(
    human_summaries: list[dict[str, Any]],
    nexo_summaries: list[dict[str, Any]],
    *,
    synthetic: bool = False,
) -> dict[str, Any]:
    n = min(len(human_summaries), len(nexo_summaries))
    if n < 3:
        return {"status": "INSUFFICIENT_SAMPLE", "n": n, "crs_version": "crs_v1", "synthetic": synthetic}
    human_recovery = [float(s.get("recovery_episodes", 0)) for s in human_summaries[:n]]
    nexo_crs = [float((s.get("crs") or {}).get("value", 0)) for s in nexo_summaries[:n]]
    return {
        "status": "PIPELINE_READY" if synthetic else "AWAITING_HUMAN_DATA",
        "n": n,
        "crs_version": "crs_v1",
        "pearson_vs_human_recovery": pearson_correlation(nexo_crs, human_recovery),
        "ci": bootstrap_ci(nexo_crs, human_recovery),
        "synthetic": synthetic,
        "disclaimer": "SYNTHETIC_PIPELINE_TEST — NOT HUMAN VALIDATION" if synthetic else "",
    }
