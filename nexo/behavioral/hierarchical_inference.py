"""Inferencia jerárquica por capa de ablación (Sprint 30)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


_LAYER_MAP = {
    "abl_no_memory": "memory",
    "abl_no_executive": "executive",
    "abl_no_pfc": "executive",
    "abl_no_learning": "learning",
    "abl_no_consciousness": "consciousness",
    "abl_no_social": "social",
    "abl_no_sleep": "sleep",
}


def ablation_layer(ablation_id: str) -> str:
    if ablation_id == "integrated_full":
        return "baseline"
    return _LAYER_MAP.get(ablation_id, "other")


def summarize_hierarchical_effects(effects: list[dict[str, Any]]) -> dict[str, Any]:
    by_layer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for effect in effects:
        layer = ablation_layer(str(effect.get("ablation_id", "")))
        by_layer[layer].append(effect)
        by_task[str(effect.get("task_id", ""))].append(effect)

    def _layer_stats(items: list[dict[str, Any]]) -> dict[str, Any]:
        if not items:
            return {"n_effects": 0}
        ds = [abs(float(it.get("cohens_d", 0.0))) for it in items]
        sig = sum(1 for it in items if it.get("significant_ci_excludes_zero") or it.get("significant_fdr_05"))
        return {
            "n_effects": len(items),
            "mean_abs_cohens_d": round(sum(ds) / len(ds), 6),
            "max_abs_cohens_d": round(max(ds), 6),
            "n_significant": sig,
        }

    return {
        "n_effects": len(effects),
        "by_layer": {layer: _layer_stats(items) for layer, items in sorted(by_layer.items())},
        "by_task": {
            task: {"n_effects": len(items), "mean_abs_cohens_d": round(
                sum(abs(float(it.get("cohens_d", 0.0))) for it in items) / len(items), 6
            ) if items else 0.0}
            for task, items in sorted(by_task.items())
        },
    }


def enrich_statistics_with_hierarchy(stats: dict[str, Any]) -> dict[str, Any]:
    hierarchy = summarize_hierarchical_effects(stats.get("effect_sizes", []))
    return {**stats, "hierarchical_inference": hierarchy, "hierarchical_inference_enabled": True}
