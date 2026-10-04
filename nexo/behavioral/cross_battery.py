"""Comparación entre informes de baterías integradas (Sprint 20)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_battery_report(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _aggregate_primary(results: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, float]]:
    """Media por tarea × ablación × métrica primaria."""
    buckets: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in results:
        task_id = str(row["task_id"])
        ablation_id = str(row["ablation_id"])
        for metric, val in row.get("primary_metrics", {}).items():
            buckets[(task_id, ablation_id, str(metric))].append(float(val))
    out: dict[tuple[str, str, str], dict[str, float]] = {}
    for key, vals in buckets.items():
        out[key] = {"mean": sum(vals) / len(vals), "n": float(len(vals))}
    return out


def compare_battery_reports(
    labeled_reports: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Compara medias primarias entre etiquetas de batería (p. ej. v3 vs v4)."""
    aggregates = {label: _aggregate_primary(rows) for label, rows in labeled_reports.items()}
    labels = sorted(aggregates.keys())
    if len(labels) < 2:
        return {"labels": labels, "comparisons": [], "n_labels": len(labels)}

    base_label = labels[0]
    base = aggregates[base_label]
    comparisons: list[dict[str, Any]] = []
    keys = sorted(set().union(*(agg.keys() for agg in aggregates.values())))
    for key in keys:
        task_id, ablation_id, metric = key
        entry: dict[str, Any] = {
            "task_id": task_id,
            "ablation_id": ablation_id,
            "metric": metric,
            "values": {},
            "deltas_vs_base": {},
        }
        base_mean = base.get(key, {}).get("mean")
        for label in labels:
            mean = aggregates[label].get(key, {}).get("mean")
            if mean is not None:
                entry["values"][label] = round(mean, 6)
                if base_mean is not None and label != base_label:
                    entry["deltas_vs_base"][label] = round(mean - base_mean, 6)
        if len(entry["values"]) >= 2:
            comparisons.append(entry)
    return {
        "labels": labels,
        "base_label": base_label,
        "n_comparisons": len(comparisons),
        "comparisons": comparisons,
    }


def export_cross_battery(
    report_paths: dict[str, Path],
    output_path: Path,
) -> dict[str, Any]:
    labeled = {label: load_battery_report(path) for label, path in report_paths.items()}
    payload = compare_battery_reports(labeled)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "exported": True,
        "path": str(output_path),
        "n_comparisons": payload["n_comparisons"],
        "labels": payload["labels"],
    }
