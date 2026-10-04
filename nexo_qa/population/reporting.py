"""Population reporting — JSON, Markdown, CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from nexo_qa.population.aggregator import PopulationResult
from nexo_qa.population.clustering import FailureClusterer
from nexo_qa.population.models import RunExecutionRecord
from nexo_qa.population.state import PopulationState


def build_population_report(
    result: PopulationResult,
    *,
    rare_critical: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "report_type": "population_report",
        "schema_version": 1,
        "result": result.to_dict(),
        "rare_critical_findings": rare_critical or [],
        "disclaimer_en": "These are distributions of NEXO simulated runs. They are not calibrated estimates of real human population behavior.",
        "disclaimer_es": "Estas son distribuciones de ejecuciones simuladas de NEXO. No son estimaciones calibradas de conducta de población humana real.",
    }


def write_population_report_json(path: Path | str, report: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_population_report_markdown(report: dict[str, Any]) -> str:
    result = report.get("result") or {}
    lines = [
        "# Population Report",
        "",
        "## Executive Summary",
        "",
        f"- **Population:** {result.get('population_id')}",
        f"- **Planned runs:** {result.get('planned_runs')}",
        f"- **Valid cognitive runs:** {result.get('valid_runs')}",
        f"- **Infrastructure failures:** {result.get('infrastructure_failures')}",
        "",
        "## Cohorts",
        "",
    ]
    for cid, cohort in (result.get("cohorts") or {}).items():
        lines.append(f"### {cid}")
        lines.append(f"- Valid runs: {cohort.get('n_valid')} (denominator: {cohort.get('valid_runs_denominator')})")
        ncfs = (cohort.get("metric_distributions") or {}).get("ncfs_v1") or {}
        lines.append(f"- Median NCFS: {ncfs.get('median')} ({ncfs.get('status')})")
        lines.append("")
    lines.extend([
        "## Failure Clusters",
        "",
    ])
    for cluster in result.get("failure_clusters") or []:
        lines.append(
            f"- **{cluster.get('failure_type')}** — simulation prevalence {cluster.get('simulation_prevalence')}, runs {len(cluster.get('affected_run_ids') or [])}"
        )
    if report.get("rare_critical_findings"):
        lines.extend(["", "## Rare High-Severity Findings", ""])
        for r in report["rare_critical_findings"]:
            lines.append(f"- {r.get('failure_type')} ({r.get('cluster_id')})")
    lines.extend(["", report.get("disclaimer_en", ""), ""])
    return "\n".join(lines)


def write_population_report_md(path: Path | str, report: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_population_report_markdown(report), encoding="utf-8")
    return path


def write_runs_csv(path: Path | str, records: list[RunExecutionRecord]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["run_id", "cohort_id", "persona_id", "seed", "task_id", "status", "ncfs", "crs"],
        )
        w.writeheader()
        for rec in records:
            summary = rec.p6_summary or {}
            w.writerow(
                {
                    "run_id": rec.plan.run_id,
                    "cohort_id": rec.plan.cohort_id,
                    "persona_id": rec.plan.persona_id,
                    "seed": rec.plan.seed,
                    "task_id": rec.plan.task_id,
                    "status": rec.status.value,
                    "ncfs": (summary.get("ncfs") or {}).get("value"),
                    "crs": (summary.get("crs") or {}).get("value"),
                }
            )
    return path


def aggregate_and_report(
    *,
    population_root: Path | str,
    state: PopulationState,
    versions: dict[str, str] | None = None,
) -> dict[str, Any]:
    from nexo_qa.population.aggregator import PopulationAggregator

    root = Path(population_root)
    records = list(state.records.values())
    clusterer = FailureClusterer()
    cluster_objs = clusterer.cluster(records)
    clusters = [c.to_dict() for c in cluster_objs]
    rare = clusterer.rare_critical(cluster_objs)

    agg = PopulationAggregator()
    result = agg.aggregate(
        population_id=state.population_id,
        spec_hash=state.spec_hash,
        records=records,
        clusters=clusters,
        versions=versions or {},
    )
    report = build_population_report(result, rare_critical=rare)
    write_population_report_json(root / "population_report.json", report)
    write_population_report_md(root / "population_report.md", report)
    write_runs_csv(root / "runs.csv", records)
    agg_dir = root / "aggregates"
    agg_dir.mkdir(exist_ok=True)
    (agg_dir / "cohorts.json").write_text(json.dumps(result.to_dict()["cohorts"], indent=2), encoding="utf-8")
    (agg_dir / "failures.json").write_text(json.dumps(clusters, indent=2), encoding="utf-8")
    return report
