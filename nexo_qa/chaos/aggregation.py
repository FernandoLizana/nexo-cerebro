"""Population chaos aggregation and cohort sensitivity."""

from __future__ import annotations

import statistics
from typing import Any

from nexo_qa.chaos.models import PairedChaosDelta
from nexo_qa.chaos.pairs import status_degradation_rate
from nexo_qa.population.aggregator import compute_distribution


def aggregate_population_chaos(
    deltas: list[PairedChaosDelta],
    *,
    chaos_id: str,
) -> dict[str, Any]:
    valid = [d for d in deltas if d.validity == "VALID"]
    invalid = [d for d in deltas if d.validity != "VALID"]
    ncfs_deltas = [
        float(d.metric_deltas["ncfs_delta"])
        for d in valid
        if d.metric_deltas.get("ncfs_delta") is not None
    ]
    crs_deltas = [
        float(d.metric_deltas["crs_delta"])
        for d in valid
        if d.metric_deltas.get("crs_delta") is not None
    ]
    return {
        "chaos_id": chaos_id,
        "valid_pairs": len(valid),
        "invalid_pairs": len(invalid),
        "ncfs_delta_distribution": compute_distribution(ncfs_deltas).to_dict(),
        "crs_delta_distribution": compute_distribution(crs_deltas).to_dict(),
        "status_degradation": status_degradation_rate(deltas),
        "disclaimer": "simulation paired deltas — not human resilience estimates",
    }


def cohort_sensitivity_matrix(
    deltas: list[PairedChaosDelta],
    *,
    persona_id: str,
    perturbation_types: dict[str, str],
) -> list[dict[str, Any]]:
    """Rows: persona × perturbation with median delta."""
    rows: list[dict[str, Any]] = []
    by_pert: dict[str, list[float]] = {}
    for d in deltas:
        if d.validity != "VALID":
            continue
        pid = perturbation_types.get(d.pair_id, "UNKNOWN")
        val = d.metric_deltas.get("ncfs_delta")
        if val is not None:
            by_pert.setdefault(pid, []).append(float(val))
    for pert, vals in sorted(by_pert.items()):
        med = statistics.median(vals) if vals else None
        rows.append(
            {
                "persona_id": persona_id,
                "perturbation": pert,
                "n_pairs": len(vals),
                "median_ncfs_delta": round(med, 4) if med is not None else None,
                "simulation_note": True,
            }
        )
    return rows
