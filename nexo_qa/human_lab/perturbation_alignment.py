"""P8 perturbation alignment — human vs NEXO."""

from __future__ import annotations

from typing import Any

from nexo_qa.human_lab.statistics import pearson_correlation


def perturbation_alignment(
    human_deltas: list[dict[str, Any]],
    nexo_deltas: list[dict[str, Any]],
    *,
    synthetic: bool = False,
) -> dict[str, Any]:
    n = min(len(human_deltas), len(nexo_deltas))
    if n < 2:
        return {"status": "INSUFFICIENT_SAMPLE", "n": n, "synthetic": synthetic}
    h_comp = [float(d.get("completion_delta", 0)) for d in human_deltas[:n]]
    n_comp = [float(d.get("completion_delta", 0)) for d in nexo_deltas[:n]]
    return {
        "n_pairs": n,
        "completion_delta_correlation": pearson_correlation(h_comp, n_comp),
        "action_delta_correlation": pearson_correlation(
            [float(d.get("action_delta", 0)) for d in human_deltas[:n]],
            [float(d.get("action_delta", 0)) for d in nexo_deltas[:n]],
        ),
        "synthetic": synthetic,
        "disclaimer": "SYNTHETIC_PIPELINE_TEST — NOT HUMAN VALIDATION" if synthetic else "",
    }
