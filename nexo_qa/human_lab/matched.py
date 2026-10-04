"""Matched human/NEXO task design validation."""

from __future__ import annotations

from typing import Any

from nexo_qa.human_lab.models import HumanRunSummary, HumanTaskProtocol


def verify_task_version_match(
    human: HumanRunSummary | HumanTaskProtocol,
    nexo_meta: dict[str, Any],
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    h_task = getattr(human, "task_id", None) or human.task_id  # type: ignore[union-attr]
    h_ver = getattr(human, "task_version", None) or human.task_version  # type: ignore[union-attr]
    h_env = getattr(human, "environment_version", None) or human.environment_version  # type: ignore[union-attr]
    n_task = str(nexo_meta.get("task_id", ""))
    n_ver = str(nexo_meta.get("task_version", nexo_meta.get("task_version_id", "")))
    n_env = str(nexo_meta.get("environment_version", "web_lab_v1"))
    if h_task != n_task:
        issues.append(f"task_id mismatch: {h_task} vs {n_task}")
    if n_ver and h_ver != n_ver:
        issues.append(f"task_version mismatch: {h_ver} vs {n_ver}")
    if n_env and h_env != n_env:
        issues.append(f"environment_version mismatch: {h_env} vs {n_env}")
    return (len(issues) == 0, issues)


def build_matched_cells(
    human_runs: list[HumanRunSummary],
    nexo_population_ids: dict[str, str],
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for run in human_runs:
        cells.append(
            {
                "task_id": run.task_id,
                "condition": run.condition,
                "human_run_id": run.human_run_id,
                "nexo_population_id": nexo_population_ids.get(f"{run.task_id}:{run.condition}", ""),
                "task_version": run.task_version,
                "environment_version": run.environment_version,
            }
        )
    return cells
