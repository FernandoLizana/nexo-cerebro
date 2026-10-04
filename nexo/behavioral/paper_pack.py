"""Paquete paper CSV + LaTeX desde resultado integrado (Sprint 38)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


METRIC_KEYS = (
    "ticks",
    "mean_surprise",
    "final_energy",
    "final_fatigue",
    "deliberation_events",
    "memory_encodings",
    "memory_retrievals",
    "workspace_broadcasts",
    "metacognition_events",
    "social_exchanges",
    "trace_events",
    "event_count",
    "trajectory_hash",
    "metric_fingerprint",
    "replication_id",
)


def build_metrics_rows(result: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for key in METRIC_KEYS:
        val = result.get(key, "")
        rows.append({"metric": key, "value": str(val)})
    rows.append({"metric": "profile", "value": str(result.get("profile", ""))})
    rows.append({"metric": "seed", "value": str(result.get("seed", ""))})
    return rows


def export_metrics_csv(result: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(build_metrics_rows(result))
    return output_path


def export_latex_table(result: dict[str, Any], output_path: Path) -> Path:
    lines = [
        "% Auto-generated NEXO integrated metrics table",
        "\\begin{tabular}{lr}",
        "\\hline",
        "Metric & Value \\\\",
        "\\hline",
    ]
    for row in build_metrics_rows(result):
        if row["metric"] in ("trajectory_hash", "metric_fingerprint", "replication_id"):
            continue
        safe_val = row["value"].replace("_", "\\_")
        lines.append(f"{row['metric']} & {safe_val} \\\\")
    lines.extend(["\\hline", "\\end{tabular}"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def export_paper_pack(
    runtime: Any,
    result: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = export_metrics_csv(result, output_dir / "metrics.csv")
    tex_path = export_latex_table(result, output_dir / "metrics_table.tex")
    manifest = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "artifacts": {
            "metrics_csv": str(csv_path),
            "latex_table": str(tex_path),
        },
    }
    manifest_path = output_dir / "paper_pack_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "exported": True,
        "output_dir": str(output_dir),
        "metrics_csv": str(csv_path),
        "latex_table": str(tex_path),
    }
