"""Tests Sprint 10 — batería conductual y ablaciones."""

from __future__ import annotations

from nexo.ablation.profiles import ABLATION_REGISTRY, INTEGRATED_FULL
from nexo.behavioral.metrics import compute_metrics
from nexo.behavioral.tasks import (
    base_integrated_config,
    run_distractor_control_task,
    run_reproducibility_task,
    run_survival_task,
)
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_ablation_disables_memory_layer():
    cfg = ABLATION_REGISTRY["abl_no_memory"].apply(base_integrated_config())
    assert cfg.memory_mode == "legacy"
    assert cfg.executive_mode == "integrated"


def test_survival_task_returns_metrics():
    result = run_survival_task(ablation=INTEGRATED_FULL, seed=42, ticks=40)
    assert result.task_id == "survival"
    assert "survival_success" in result.primary_metrics
    assert result.primary_metrics["final_energy"] >= 0.0


def test_reproducibility_task_matches():
    result = run_reproducibility_task(ablation=INTEGRATED_FULL, seed=77, ticks=35)
    assert result.primary_metrics["trajectory_match"] == 1.0


def test_ablation_changes_trajectory():
    full = run_survival_task(ablation=INTEGRATED_FULL, seed=42, ticks=45)
    no_exec = run_survival_task(ablation=ABLATION_REGISTRY["abl_no_executive"], seed=42, ticks=45)
    assert full.details["trajectory_hash"] != no_exec.details["trajectory_hash"]


def test_evaluation_mode_emits_snapshots():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=45,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="integrated",
            evaluation_mode="integrated",
        )
    )
    result = rt.run()
    assert result["evaluation_mode"] == "integrated"
    assert result["behavior_snapshots"] >= 1


def test_integrated_battery_runner_subset():
    from experiments.integrated_battery.run_battery import run_integrated_battery

    results = run_integrated_battery(
        seeds=(42,),
        ablation_ids=("integrated_full", "abl_no_pfc"),
    )
    assert len(results) == 6
    task_ids = {r["task_id"] for r in results}
    assert task_ids == {"survival", "distractor_control", "reproducibility"}


def test_integrated_v10_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v10.yaml")
    result = rt.run(40)
    assert result["profile"] == "integrated_v10"
    assert result["evaluation_mode"] == "integrated"
