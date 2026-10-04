"""Análisis comparativo de resultados de batería vs baseline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BASELINE_ABLATION = "integrated_full"
BASELINE_LESION = "lesion_none"


@dataclass
class ComparisonEntry:
    task_id: str
    ablation_id: str
    lesion_id: str
    seed: int
    baseline_metrics: dict[str, float]
    candidate_metrics: dict[str, float]
    deltas: dict[str, float] = field(default_factory=dict)
    l1_distance: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "ablation_id": self.ablation_id,
            "lesion_id": self.lesion_id,
            "seed": self.seed,
            "baseline_metrics": self.baseline_metrics,
            "candidate_metrics": self.candidate_metrics,
            "deltas": self.deltas,
            "l1_distance": round(self.l1_distance, 6),
        }


def compare_to_baseline(
    results: list[dict[str, Any]],
    *,
    baseline_ablation: str = BASELINE_ABLATION,
    baseline_lesion: str = BASELINE_LESION,
) -> list[ComparisonEntry]:
    """Calcula deltas respecto a integrated_full + lesion_none por tarea y seed."""
    baseline_map: dict[tuple[str, int], dict[str, float]] = {}
    for row in results:
        lesion_id = str(row.get("details", {}).get("lesion_id", BASELINE_LESION))
        if row["ablation_id"] == baseline_ablation and lesion_id == baseline_lesion:
            baseline_map[(row["task_id"], int(row["seed"]))] = dict(row.get("primary_metrics", {}))

    entries: list[ComparisonEntry] = []
    for row in results:
        lesion_id = str(row.get("details", {}).get("lesion_id", BASELINE_LESION))
        key = (row["task_id"], int(row["seed"]))
        baseline = baseline_map.get(key)
        if baseline is None:
            continue
        candidate = dict(row.get("primary_metrics", {}))
        if row["ablation_id"] == baseline_ablation and lesion_id == baseline_lesion:
            deltas = {k: 0.0 for k in baseline}
        else:
            keys = sorted(set(baseline) | set(candidate))
            deltas = {k: float(candidate.get(k, 0.0)) - float(baseline.get(k, 0.0)) for k in keys}
        l1 = sum(abs(v) for v in deltas.values())
        entries.append(
            ComparisonEntry(
                task_id=row["task_id"],
                ablation_id=row["ablation_id"],
                lesion_id=lesion_id,
                seed=int(row["seed"]),
                baseline_metrics=baseline,
                candidate_metrics=candidate,
                deltas=deltas,
                l1_distance=l1,
            )
        )
    return entries


def rank_by_effect(comparisons: list[ComparisonEntry]) -> list[dict[str, Any]]:
    """Ranking de condiciones por distancia L1 agregada."""
    scores: dict[tuple[str, str], float] = {}
    counts: dict[tuple[str, str], int] = {}
    for entry in comparisons:
        if entry.ablation_id == BASELINE_ABLATION and entry.lesion_id == BASELINE_LESION:
            continue
        key = (entry.ablation_id, entry.lesion_id)
        scores[key] = scores.get(key, 0.0) + entry.l1_distance
        counts[key] = counts.get(key, 0) + 1
    ranked = []
    for (ablation_id, lesion_id), total in sorted(scores.items(), key=lambda x: -x[1]):
        n = counts[(ablation_id, lesion_id)]
        ranked.append(
            {
                "ablation_id": ablation_id,
                "lesion_id": lesion_id,
                "mean_l1_distance": round(total / max(n, 1), 6),
                "n_comparisons": n,
            }
        )
    return ranked


def export_comparison(
    comparisons: list[ComparisonEntry],
    path: Path,
) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "baseline_ablation": BASELINE_ABLATION,
        "baseline_lesion": BASELINE_LESION,
        "n_entries": len(comparisons),
        "ranking": rank_by_effect(comparisons),
        "entries": [e.to_dict() for e in comparisons],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload
