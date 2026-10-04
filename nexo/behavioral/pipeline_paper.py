"""Pipeline paper E2E: batería → tablas → figuras (Sprint 45)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_pipeline_paper(
    manifest_path: Path,
    *,
    output_dir: Path,
    meta_root: Path | None = None,
    meta_output: Path | None = None,
    cross_reports: dict[str, Path] | None = None,
    cross_output: Path | None = None,
    pipeline_output: Path | None = None,
) -> dict[str, Any]:
    from nexo.behavioral.battery_paper import export_battery_paper
    from nexo.behavioral.orchestration import run_integrated_pipeline
    from nexo.behavioral.paper_figures import export_paper_figures

    summary = run_integrated_pipeline(
        manifest_path,
        meta_root=meta_root,
        meta_output=meta_output,
        cross_reports=cross_reports,
        cross_output=cross_output,
        pipeline_output=None,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    battery = summary.get("battery") or {}
    report_path = Path(battery.get("json", ""))
    paper_artifacts: dict[str, Any] = {}
    if report_path.is_file():
        paper_dir = output_dir / "battery_paper"
        paper_artifacts["battery_paper"] = export_battery_paper(
            {"battery": report_path},
            paper_dir,
        )
        figures_dir = output_dir / "figures"
        paper_artifacts["paper_figures"] = export_paper_figures(report_path, figures_dir)
    summary["pipeline_paper"] = {
        "output_dir": str(output_dir),
        "artifacts": paper_artifacts,
    }
    if pipeline_output is not None:
        pipeline_output.parent.mkdir(parents=True, exist_ok=True)
        pipeline_output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        summary["pipeline_export"] = str(pipeline_output)
    return summary


def run_pipeline_paper_auto(
    *,
    manifest_path: Path,
    output_dir: Path,
    result: dict[str, Any],
    pipeline_output: Path | None = None,
    meta_root: Path | None = None,
    meta_output: Path | None = None,
    cross_reports: dict[str, Path] | None = None,
    cross_output: Path | None = None,
    build_latex: bool = True,
) -> dict[str, Any]:
    """Pipeline paper completo + LaTeX maestro opcional (Sprint 49)."""
    summary = run_pipeline_paper(
        manifest_path,
        output_dir=output_dir,
        meta_root=meta_root,
        meta_output=meta_output,
        cross_reports=cross_reports,
        cross_output=cross_output,
        pipeline_output=pipeline_output,
    )
    if build_latex:
        from nexo.behavioral.latex_master import export_latex_master

        paper_dir = output_dir / "battery_paper"
        fig_dir = output_dir / "figures"
        latex_dir = output_dir / "latex_master"
        summary["latex_master"] = export_latex_master(
            result,
            latex_dir,
            battery_paper_dir=paper_dir if paper_dir.is_dir() else None,
            figures_dir=fig_dir if fig_dir.is_dir() else None,
        )
    return summary
