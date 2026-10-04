"""Exportación de benchmarks conductuales integrados."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def summarize_battery(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Agrega métricas primarias por tarea × ablación × lesión."""
    groups: dict[tuple[str, str, str], list[dict[str, float]]] = defaultdict(list)
    for row in results:
        lesion_id = str(row.get("details", {}).get("lesion_id", "lesion_none"))
        key = (row["task_id"], row["ablation_id"], lesion_id)
        groups[key].append(dict(row.get("primary_metrics", {})))

    aggregates: list[dict[str, Any]] = []
    for (task_id, ablation_id, lesion_id), metric_rows in sorted(groups.items()):
        keys = sorted({k for m in metric_rows for k in m})
        entry: dict[str, Any] = {
            "task_id": task_id,
            "ablation_id": ablation_id,
            "lesion_id": lesion_id,
            "n_runs": len(metric_rows),
        }
        for key in keys:
            vals = [float(m[key]) for m in metric_rows if key in m]
            if vals:
                entry[f"{key}_mean"] = sum(vals) / len(vals)
        aggregates.append(entry)

    return {
        "total_runs": len(results),
        "groups": len(aggregates),
        "aggregates": aggregates,
    }


def export_benchmark(
    results: list[dict[str, Any]],
    json_path: Path,
    *,
    csv_path: Path | None = None,
) -> dict[str, Any]:
    summary = summarize_battery(results)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"results": results, "summary": summary}
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if csv_path is not None:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        aggregates = summary["aggregates"]
        if aggregates:
            fieldnames = sorted({k for row in aggregates for k in row})
            with csv_path.open("w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(aggregates)

    return summary
