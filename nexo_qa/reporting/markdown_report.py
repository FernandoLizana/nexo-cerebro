"""Markdown cognitive QA report."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_markdown_report(json_report: dict[str, Any]) -> str:
    summary = json_report.get("summary") or {}
    lines = [
        "# Cognitive QA Report",
        "",
        "## Executive Summary",
        "",
        f"- **Run ID:** {summary.get('run_id', 'unknown')}",
        f"- **Assessment:** {summary.get('assessment_status', 'unknown')}",
        f"- **Goal result:** {summary.get('result', 'unknown')}",
        f"- **Failures:** {summary.get('failure_count', 0)}",
        f"- **Episodes:** {summary.get('episode_count', 0)}",
        "",
        "## Run Metadata",
        "",
        f"- **Persona:** {summary.get('persona_id') or 'none'}",
        f"- **Goal:** {summary.get('goal_description', '')}",
        "",
        "## Core Metrics",
        "",
    ]
    for mid, mval in (summary.get("core_metrics") or {}).items():
        if isinstance(mval, dict):
            lines.append(f"- **{mid}:** {mval.get('value')} ({mval.get('status')})")
    lines.extend([
        "",
        "## NCFS",
        "",
        f"- **Value:** {(summary.get('ncfs') or {}).get('value')}",
        f"- **Coverage:** {(summary.get('ncfs') or {}).get('coverage')}",
        f"- **Disclaimer:** simulation-derived; not human-calibrated",
        "",
        "## EHFP",
        "",
        f"- **Value:** {(summary.get('ehfp') or {}).get('value')}/100",
        f"- **Label:** {(summary.get('ehfp') or {}).get('label')}",
        f"- **Is probability:** NO",
        "",
        "## CRS",
        "",
        f"- **Value:** {(summary.get('crs') or {}).get('value')}",
        "",
        "## Top Issues",
        "",
    ])
    for issue in summary.get("top_issues") or []:
        lines.append(f"- **{issue.get('title')}** — severity {issue.get('severity')}, occurrences {issue.get('occurrences')}")
    lines.extend([
        "",
        "## Failure Certificates",
        "",
    ])
    for cid in summary.get("certificate_ids") or []:
        lines.append(f"- {cid}")
    lines.extend([
        "",
        "## Limitations",
        "",
        json_report.get("disclaimer_en", ""),
        "",
        json_report.get("disclaimer_es", ""),
        "",
    ])
    return "\n".join(lines)


def write_markdown_report(path: Path | str, json_report: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_markdown_report(json_report), encoding="utf-8")
    return path
