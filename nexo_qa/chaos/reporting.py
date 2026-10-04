"""Chaos reporting — JSON and Markdown."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from nexo_qa.chaos.aggregation import aggregate_population_chaos, cohort_sensitivity_matrix
from nexo_qa.chaos.models import ChaosPlan, PairedChaosDelta
from nexo_qa.chaos.pairs import status_degradation_rate
from nexo_qa.chaos.runner import ChaosState
from nexo_qa.population.clustering import FailureClusterer


def build_chaos_report(
    *,
    chaos_id: str,
    plan: ChaosPlan,
    state: ChaosState,
    deltas: list[PairedChaosDelta],
    injection_coverage: dict[str, Any],
) -> dict[str, Any]:
    valid_deltas = [d for d in deltas if d.validity == "VALID"]
    pert_types = {p.pair_id: p.perturbation.type for p in plan.pairs}
    persona = plan.pairs[0].persona_id if plan.pairs else "unknown"
    records = list(state.records.values())
    clusters = [c.to_dict() for c in FailureClusterer().cluster(records)]
    rare = FailureClusterer().rare_critical(FailureClusterer().cluster(records))
    return {
        "report_type": "chaos_report",
        "schema_version": 1,
        "chaos_id": chaos_id,
        "executive_summary": {
            "planned_pairs": len(plan.pairs),
            "valid_pairs": len(valid_deltas),
            "invalid_pairs": len(deltas) - len(valid_deltas),
        },
        "baseline_definition": {"condition": "BASELINE", "paired": True},
        "perturbation_definitions": [p.perturbation.to_dict() for p in plan.pairs],
        "injection_coverage": injection_coverage,
        "pair_coverage": {
            "total": len(deltas),
            "valid": len(valid_deltas),
            "invalid": len(deltas) - len(valid_deltas),
        },
        "paired_metric_deltas": [d.to_dict() for d in valid_deltas],
        "invalid_pairs": [d.to_dict() for d in deltas if d.validity != "VALID"],
        "status_degradation": status_degradation_rate(deltas),
        "population_chaos": aggregate_population_chaos(deltas, chaos_id=chaos_id),
        "cohort_sensitivity": cohort_sensitivity_matrix(deltas, persona_id=persona, perturbation_types=pert_types),
        "failure_clusters": clusters,
        "rare_critical_findings": rare,
        "disclaimer_en": (
            "These are differences observed in NEXO simulated runs. "
            "They are not calibrated estimates of human behavior or human resilience."
        ),
        "disclaimer_es": (
            "Estas son diferencias observadas en ejecuciones simuladas de NEXO. "
            "No son estimaciones calibradas de conducta humana ni resiliencia humana."
        ),
    }


def write_chaos_report_json(path: Path | str, report: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_chaos_report_markdown(report: dict[str, Any]) -> str:
    summary = report.get("executive_summary") or {}
    lines = [
        "# Chaos Report",
        "",
        "## Executive Summary",
        f"- Planned pairs: {summary.get('planned_pairs')}",
        f"- Valid pairs: {summary.get('valid_pairs')}",
        f"- Invalid pairs: {summary.get('invalid_pairs')}",
        "",
        "## Injection Coverage",
        json.dumps(report.get("injection_coverage") or {}, indent=2),
        "",
        "## Status Degradation",
        json.dumps(report.get("status_degradation") or {}, indent=2),
        "",
        report.get("disclaimer_en", ""),
    ]
    return "\n".join(lines)


def write_paired_csv(path: Path | str, deltas: list[PairedChaosDelta]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["pair_id", "validity", "baseline_run_id", "perturbed_run_id", "ncfs_delta", "status_change"],
        )
        w.writeheader()
        for d in deltas:
            w.writerow(
                {
                    "pair_id": d.pair_id,
                    "validity": d.validity,
                    "baseline_run_id": d.baseline_run_id,
                    "perturbed_run_id": d.perturbed_run_id,
                    "ncfs_delta": d.metric_deltas.get("ncfs_delta"),
                    "status_change": d.status_change,
                }
            )
    return path
