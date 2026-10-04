"""Batería completa + estadística FDR exportada (Sprint 48)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def run_battery_full(
    manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    from nexo.behavioral.manifest import execute_manifest

    output_dir.mkdir(parents=True, exist_ok=True)
    summary = execute_manifest(manifest_path)
    report_json = Path(summary.get("json", ""))
    stats_path = Path(summary.get("statistics", ""))
    payload = {
        "manifest": str(manifest_path),
        "report_json": str(report_json) if report_json.is_file() else None,
        "statistics_json": str(stats_path) if stats_path.is_file() else None,
        "total_runs": summary.get("total_runs"),
        "fdr_correction": summary.get("fdr_correction"),
        "inference_enabled": summary.get("inference_enabled"),
        "hierarchical_inference": summary.get("hierarchical_inference"),
        "statistics_aggregates": summary.get("statistics_aggregates"),
        "statistics_effects": summary.get("statistics_effects"),
        "battery_summary": summary,
    }
    out_path = output_dir / "battery_full_summary.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "exported": True,
        "output_dir": str(output_dir),
        "summary_path": str(out_path),
        **{k: payload[k] for k in ("total_runs", "fdr_correction", "statistics_effects")},
    }
