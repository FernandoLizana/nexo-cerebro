"""Estadística descriptiva sobre resultados de batería integrada."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from nexo.behavioral.comparison import BASELINE_ABLATION, BASELINE_LESION, compare_to_baseline
from nexo.behavioral.correction import apply_fdr_to_effects
from nexo.behavioral.hierarchical_inference import enrich_statistics_with_hierarchy
from nexo.behavioral.inference import enrich_effects_with_inference
from nexo.behavioral.permutation import permutation_p_value


def _mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    m = sum(values) / len(values)
    if len(values) < 2:
        return m, 0.0
    var = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return m, math.sqrt(var)


def bootstrap_ci(
    values: list[float],
    *,
    n_boot: int = 256,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Media observada y percentiles bootstrap para IC aproximado."""
    if not values:
        return 0.0, 0.0, 0.0
    if len(values) == 1:
        return values[0], values[0], values[0]
    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype=np.float64)
    boots = [
        float(np.mean(rng.choice(arr, size=len(arr), replace=True)))
        for _ in range(n_boot)
    ]
    boots.sort()
    lo_idx = max(0, int((alpha / 2) * n_boot))
    hi_idx = min(n_boot - 1, int((1 - alpha / 2) * n_boot) - 1)
    return float(np.mean(arr)), boots[lo_idx], boots[hi_idx]


def cohens_d(group_a: list[float], group_b: list[float]) -> float:
    if len(group_a) < 1 or len(group_b) < 1:
        return 0.0
    ma, sa = _mean_std(group_a)
    mb, sb = _mean_std(group_b)
    pooled = math.sqrt((sa**2 + sb**2) / 2)
    if pooled < 1e-9:
        return 0.0
    return (ma - mb) / pooled


def aggregate_by_condition(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrega métricas primarias por tarea × ablación × lesión a través de seeds."""
    buckets: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for row in results:
        lesion_id = str(row.get("details", {}).get("lesion_id", BASELINE_LESION))
        for key, val in row.get("primary_metrics", {}).items():
            buckets[(row["task_id"], row["ablation_id"], lesion_id, key)].append(float(val))

    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for (task_id, ablation_id, lesion_id, metric), vals in sorted(buckets.items()):
        key = (task_id, ablation_id, lesion_id)
        if key not in grouped:
            grouped[key] = {
                "task_id": task_id,
                "ablation_id": ablation_id,
                "lesion_id": lesion_id,
                "n_seeds": len(
                    {
                        int(r["seed"])
                        for r in results
                        if r["task_id"] == task_id
                        and r["ablation_id"] == ablation_id
                        and str(r.get("details", {}).get("lesion_id", BASELINE_LESION)) == lesion_id
                    }
                ),
                "metrics": {},
            }
        mean, std = _mean_std(vals)
        _, ci_lo, ci_hi = bootstrap_ci(vals, seed=abs(hash((task_id, ablation_id, lesion_id, metric))) % 10_000)
        grouped[key]["metrics"][metric] = {
            "mean": round(mean, 6),
            "std": round(std, 6),
            "ci_low": round(ci_lo, 6),
            "ci_high": round(ci_hi, 6),
            "n": len(vals),
        }
    return list(grouped.values())


def effect_sizes_vs_baseline(
    results: list[dict[str, Any]],
    *,
    include_permutation: bool = False,
) -> list[dict[str, Any]]:
    """Cohen's d por métrica vs baseline para cada condición candidata."""
    baseline_vals: dict[tuple[str, str], list[float]] = defaultdict(list)
    candidate_vals: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)

    for row in results:
        lesion_id = str(row.get("details", {}).get("lesion_id", BASELINE_LESION))
        task_id = row["task_id"]
        for metric, val in row.get("primary_metrics", {}).items():
            fval = float(val)
            if row["ablation_id"] == BASELINE_ABLATION and lesion_id == BASELINE_LESION:
                baseline_vals[(task_id, metric)].append(fval)
            else:
                candidate_vals[(task_id, row["ablation_id"], lesion_id, metric)].append(fval)

    effects: list[dict[str, Any]] = []
    for (task_id, ablation_id, lesion_id, metric), vals in sorted(candidate_vals.items()):
        base = baseline_vals.get((task_id, metric), [])
        if not base:
            continue
        entry: dict[str, Any] = {
            "task_id": task_id,
            "ablation_id": ablation_id,
            "lesion_id": lesion_id,
            "metric": metric,
            "cohens_d": round(cohens_d(vals, base), 6),
            "n_candidate": len(vals),
            "n_baseline": len(base),
            "mean_delta": round(_mean_std(vals)[0] - _mean_std(base)[0], 6),
        }
        if include_permutation:
            entry["permutation_p"] = round(
                permutation_p_value(base, vals, seed=abs(hash((task_id, ablation_id, lesion_id, metric))) % 10_000),
                6,
            )
        effects.append(entry)
    return effects


def summarize_statistics(
    results: list[dict[str, Any]],
    *,
    include_permutation: bool = False,
    include_fdr_correction: bool = False,
    include_inference: bool = False,
    include_hierarchical: bool = False,
) -> dict[str, Any]:
    effects = effect_sizes_vs_baseline(results, include_permutation=include_permutation)
    if include_fdr_correction and include_permutation:
        effects = apply_fdr_to_effects(effects)
    if include_inference:
        effects = enrich_effects_with_inference(results, effects)
    payload = {
        "total_runs": len(results),
        "aggregates": aggregate_by_condition(results),
        "effect_sizes": effects,
        "comparisons": len(compare_to_baseline(results)),
        "permutation_enabled": include_permutation,
        "fdr_correction_enabled": include_fdr_correction,
        "inference_enabled": include_inference,
        "hierarchical_inference_enabled": include_hierarchical,
    }
    if include_hierarchical:
        payload = enrich_statistics_with_hierarchy(payload)
    return payload


def export_statistics(
    results: list[dict[str, Any]],
    path: Path,
    *,
    include_permutation: bool = False,
    include_fdr_correction: bool = False,
    include_inference: bool = False,
    include_hierarchical: bool = False,
) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = summarize_statistics(
        results,
        include_permutation=include_permutation,
        include_fdr_correction=include_fdr_correction,
        include_inference=include_inference,
        include_hierarchical=include_hierarchical,
    )
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload
