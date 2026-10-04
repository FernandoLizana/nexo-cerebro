"""Tests Sprints 39–42 — unificación motora, env legacy, battery paper, publicación completa."""

from __future__ import annotations

import json
from pathlib import Path

from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.behavioral.battery_paper import export_battery_paper
from nexo.behavioral.deliberation_unified import export_deliberation_unified, summarize_deliberation_unified
from nexo.behavioral.publication import export_full_publication_bundle
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import (
    run_deliberation_conflict_task,
    run_world2d_legacy_env_navigation_task,
)
from nexo.demo.world2d_legacy_env import World2DLegacyEnvWorld
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_world2d_legacy_env_world():
    world = World2DLegacyEnvWorld(seed=42, legacy_env_enabled=True)
    assert world.furniture_count >= 8
    assert world.env_fidelity_score() > 0.0
    world.apply_action("explore")
    assert len(world.rooms_visited) >= 1


def test_world2d_legacy_env_navigation_task():
    result = run_world2d_legacy_env_navigation_task(ablation=INTEGRATED_FULL, seed=42, ticks=40)
    assert result.task_id == "world2d_legacy_env_navigation"
    assert result.primary_metrics["env_fidelity"] > 0.0


def test_deliberation_conflict_task():
    result = run_deliberation_conflict_task(ablation=INTEGRATED_FULL, seed=42, ticks=35)
    assert result.task_id == "deliberation_conflict_resolution"
    assert result.primary_metrics["unified_events"] >= 0.0


def test_task_registry_fase6():
    assert "deliberation_conflict_resolution" in TASK_REGISTRY
    assert "world2d_legacy_env_navigation" in TASK_REGISTRY


def test_deliberation_unified_motor_events():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=15,
            deliberation_bridge_mode="integrated",
            deliberation_fusion_mode="integrated",
            deliberation_unified_mode="integrated",
            legacy_adapter_mode="integrated",
        )
    )
    rt.run()
    summary = summarize_deliberation_unified(rt)
    assert summary["motor_authority"] == "unified"
    unified = [ev for ev in rt.state_store.event_log if ev.event_type == "action.unified"]
    assert len(unified) >= 1


def test_deliberation_unified_export(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=12,
            deliberation_unified_mode="integrated",
            legacy_adapter_mode="integrated",
        )
    )
    result = rt.run()
    out = tmp_path / "unified.json"
    meta = export_deliberation_unified(rt, result, out)
    assert meta["exported"] is True
    assert out.exists()


def test_battery_paper_export(tmp_path: Path):
    report = tmp_path / "mini.json"
    report.write_text(
        json.dumps({
            "results": [
                {
                    "task_id": "survival",
                    "ablation_id": "integrated_full",
                    "seed": 42,
                    "primary_metrics": {"survival_score": 0.8},
                }
            ]
        }),
        encoding="utf-8",
    )
    meta = export_battery_paper({"mini": report}, tmp_path / "paper")
    assert meta["exported"] is True
    assert (tmp_path / "paper" / "mini_battery.csv").exists()


def test_full_publication_bundle(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=10,
            full_publication_mode="integrated",
            paper_pack_mode="integrated",
        )
    )
    result = rt.run()
    paper_dir = tmp_path / "paper"
    from nexo.behavioral.paper_pack import export_paper_pack

    export_paper_pack(rt, result, paper_dir)
    meta = export_full_publication_bundle(
        rt,
        result,
        tmp_path / "full",
        paper_pack_dir=paper_dir,
    )
    assert meta["full_publication"] is True
    assert (tmp_path / "full" / "paper_pack" / "metrics.csv").exists()


def test_integrated_v38_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v38.yaml")
    result = rt.run(ticks=12)
    assert result["profile"] == "integrated_v38"
    assert result["paper_pack_mode"] == "integrated"


def test_integrated_v42_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v42.yaml")
    result = rt.run(ticks=12)
    assert result["profile"] == "integrated_v42"
    assert result["deliberation_unified_mode"] == "integrated"
    assert result["world2d_legacy_env_mode"] == "integrated"
    assert result["full_publication_mode"] == "integrated"
