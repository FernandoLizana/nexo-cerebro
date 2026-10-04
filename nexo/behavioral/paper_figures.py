"""Figuras SVG desde reportes de batería — sin dependencias extra (Sprint 44)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _normalize_results(report: dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    if isinstance(report, list):
        return [r for r in report if isinstance(r, dict)]
    results = report.get("results") or report.get("task_results") or []
    if isinstance(results, dict):
        return list(results.values())
    return [r for r in results if isinstance(r, dict)]


def aggregate_task_scores(results: list[dict[str, Any]]) -> dict[str, float]:
    scores: dict[str, list[float]] = {}
    for item in results:
        task_id = str(item.get("task_id", ""))
        primary = item.get("primary_metrics") or {}
        if not primary:
            continue
        val = next(iter(primary.values()))
        try:
            scores.setdefault(task_id, []).append(float(val))
        except (TypeError, ValueError):
            continue
    return {k: sum(v) / len(v) for k, v in scores.items() if v}


def render_bar_chart_svg(scores: dict[str, float], *, width: int = 640, height: int = 320) -> str:
    if not scores:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            '<text x="20" y="40">No data</text></svg>'
        )
    margin = 48
    bar_w = max(20, (width - 2 * margin) // max(len(scores), 1) - 8)
    max_val = max(scores.values()) or 1.0
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<rect width="{width}" height="{height}" fill="#fafafa"/>',
        f'<text x="{margin}" y="24" font-size="14" font-family="sans-serif">NEXO Battery Task Scores</text>',
    ]
    for i, (task, val) in enumerate(scores.items()):
        x = margin + i * (bar_w + 8)
        h = int((height - 2 * margin) * (val / max_val))
        y = height - margin - h
        label = task[:12].replace("_", " ")
        lines.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" fill="#3b82f6"/>')
        lines.append(f'<text x="{x}" y="{height - margin + 14}" font-size="9" font-family="sans-serif">{label}</text>')
        lines.append(f'<text x="{x}" y="{y - 4}" font-size="9" font-family="sans-serif">{val:.2f}</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def export_paper_figures(
    report_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not report_path.is_file():
        return {"exported": False, "reason": "report_not_found", "path": str(report_path)}
    raw = json.loads(report_path.read_text(encoding="utf-8"))
    scores = aggregate_task_scores(_normalize_results(raw))
    svg = render_bar_chart_svg(scores)
    svg_path = output_dir / "battery_scores.svg"
    svg_path.write_text(svg, encoding="utf-8")
    tex_snippet = output_dir / "figure_battery.tex"
    tex_snippet.write_text(
        "\\begin{figure}[h]\n"
        "  \\centering\n"
        f"  \\includesvg[width=0.85\\linewidth]{{{svg_path.name}}}\n"
        "  \\caption{NEXO integrated battery task scores}\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )
    manifest = {
        "report": str(report_path),
        "scores": scores,
        "artifacts": {
            "svg": str(svg_path),
            "latex_snippet": str(tex_snippet),
        },
    }
    (output_dir / "figures_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {
        "exported": True,
        "output_dir": str(output_dir),
        "n_tasks": len(scores),
        "svg": str(svg_path),
        "latex_snippet": str(tex_snippet),
    }
