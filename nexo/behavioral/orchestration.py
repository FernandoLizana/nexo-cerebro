"""Pipeline integrado batería + meta + cross (Sprint 26)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_integrated_pipeline(
    manifest_path: Path,
    *,
    meta_root: Path | None = None,
    meta_output: Path | None = None,
    cross_reports: dict[str, Path] | None = None,
    cross_output: Path | None = None,
    pipeline_output: Path | None = None,
) -> dict[str, Any]:
    from nexo.behavioral.cross_battery import export_cross_battery
    from nexo.behavioral.manifest import execute_manifest
    from nexo.behavioral.meta_analysis import export_meta_analysis

    summary: dict[str, Any] = {"manifest_path": str(manifest_path)}
    summary["battery"] = execute_manifest(manifest_path)

    if meta_root is not None and meta_output is not None:
        summary["meta_analysis"] = export_meta_analysis(meta_root, meta_output)

    if cross_reports and cross_output is not None:
        existing = {k: v for k, v in cross_reports.items() if v.is_file()}
        if len(existing) >= 2:
            summary["cross_battery"] = export_cross_battery(existing, cross_output)

    if pipeline_output is not None:
        pipeline_output.parent.mkdir(parents=True, exist_ok=True)
        pipeline_output.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        summary["pipeline_export"] = str(pipeline_output)

    return summary
