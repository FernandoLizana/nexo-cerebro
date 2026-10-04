"""Inferencia bootstrap sobre efectos de batería (Sprint 25)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

from nexo.behavioral.comparison import BASELINE_ABLATION, BASELINE_LESION


def _collect_metric_values(
    results: list[dict[str, Any]],
) -> dict[tuple[str, str, str, str], list[float]]:
    buckets: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for row in results:
        lesion_id = str(row.get("details", {}).get("lesion_id", BASELINE_LESION))
        for metric, val in row.get("primary_metrics", {}).items():
            buckets[(row["task_id"], row["ablation_id"], lesion_id, metric)].append(float(val))
    return buckets


def bootstrap_mean_delta_ci(
    baseline: list[float],
    candidate: list[float],
    *,
    n_boot: int = 512,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float, float]:
    if not baseline or not candidate:
        return 0.0, 0.0, 0.0
    rng = np.random.default_rng(seed)
    base = np.asarray(baseline, dtype=np.float64)
    cand = np.asarray(candidate, dtype=np.float64)
    deltas = []
    for _ in range(n_boot):
        b = rng.choice(base, size=len(base), replace=True)
        c = rng.choice(cand, size=len(cand), replace=True)
        deltas.append(float(np.mean(c) - np.mean(b)))
    deltas.sort()
    lo = deltas[max(0, int((alpha / 2) * n_boot))]
    hi = deltas[min(n_boot - 1, int((1 - alpha / 2) * n_boot) - 1)]
    return float(np.mean(cand) - np.mean(base)), lo, hi


def enrich_effects_with_inference(
    results: list[dict[str, Any]],
    effects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Añade CI bootstrap sobre mean_delta a cada efecto."""
    values = _collect_metric_values(results)
    enriched: list[dict[str, Any]] = []
    for effect in effects:
        entry = dict(effect)
        key = (
            effect["task_id"],
            BASELINE_ABLATION,
            BASELINE_LESION,
            effect["metric"],
        )
        cand_key = (
            effect["task_id"],
            effect["ablation_id"],
            effect.get("lesion_id", BASELINE_LESION),
            effect["metric"],
        )
        base_vals = values.get(key, [])
        cand_vals = values.get(cand_key, [])
        mean_delta, ci_lo, ci_hi = bootstrap_mean_delta_ci(
            base_vals,
            cand_vals,
            seed=abs(hash(cand_key)) % 10_000,
        )
        entry["inference_mean_delta"] = round(mean_delta, 6)
        entry["inference_ci_low"] = round(ci_lo, 6)
        entry["inference_ci_high"] = round(ci_hi, 6)
        entry["significant_ci_excludes_zero"] = bool(ci_lo > 0 or ci_hi < 0)
        enriched.append(entry)
    return enriched
