"""Pipeline paper desde reportes de batería integrada (Sprint 41)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def load_battery_report(path: Path) -> dict[str, Any] | list[Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def extract_task_rows(report: dict[str, Any] | list[Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if isinstance(report, list):
        results = report
    else:
        results = report.get("results") or report.get("task_results") or []
        if isinstance(results, dict):
            results = list(results.values())
    for item in results:
        if not isinstance(item, dict):
            continue
        primary = item.get("primary_metrics") or {}
        rows.append({
            "task_id": str(item.get("task_id", "")),
            "ablation_id": str(item.get("ablation_id", "")),
            "seed": str(item.get("seed", "")),
            "primary_metric": str(next(iter(primary.values()), "")) if primary else "",
            "metric_name": str(next(iter(primary.keys()), "")) if primary else "",
        })
    return rows


def export_battery_csv(report_path: Path, output_path: Path) -> Path:
    report = load_battery_report(report_path)
    rows = extract_task_rows(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["task_id", "ablation_id", "seed", "metric_name", "primary_metric"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def export_battery_latex(report_path: Path, output_path: Path) -> Path:
    report = load_battery_report(report_path)
    rows = extract_task_rows(report)
    lines = [
        "% Auto-generated NEXO battery summary",
        "\\begin{tabular}{lll}",
        "\\hline",
        "Task & Ablation & Metric \\\\",
        "\\hline",
    ]
    for row in rows[:20]:
        task = row["task_id"].replace("_", "\\_")
        abl = row["ablation_id"].replace("_", "\\_")
        metric = f"{row['metric_name']}={row['primary_metric']}".replace("_", "\\_")
        lines.append(f"{task} & {abl} & {metric} \\\\")
    lines.extend(["\\hline", "\\end{tabular}"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def export_battery_paper(
    report_paths: dict[str, Path],
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, str] = {}
    for name, path in report_paths.items():
        if not path.is_file():
            continue
        csv_out = export_battery_csv(path, output_dir / f"{name}_battery.csv")
        tex_out = export_battery_latex(path, output_dir / f"{name}_battery.tex")
        artifacts[f"{name}_csv"] = str(csv_out)
        artifacts[f"{name}_tex"] = str(tex_out)
    manifest = {
        "reports": {k: str(v) for k, v in report_paths.items()},
        "artifacts": artifacts,
    }
    manifest_path = output_dir / "battery_paper_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "exported": bool(artifacts),
        "output_dir": str(output_dir),
        "artifacts": artifacts,
    }
