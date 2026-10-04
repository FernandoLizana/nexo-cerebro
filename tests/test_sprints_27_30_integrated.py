"""Tests Sprints 27–30 — legacy adapter, World2D, escala e inferencia jerárquica."""

from __future__ import annotations

import json
from pathlib import Path

from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.behavioral.hierarchical_inference import enrich_statistics_with_hierarchy, summarize_hierarchical_effects
from nexo.behavioral.legacy_adapter import export_legacy_adapter_report, summarize_legacy_adapter
from nexo.behavioral.scale_profile import benchmark_runtime_ticks, collect_scale_metrics, export_scale_profile
from nexo.behavioral.statistics import export_statistics
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import run_navigation_2d_task
from nexo.demo.world2d_lite import World2DLiteWorld
from nexo.demo.world_factory import create_world
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_world2d_lite_moves_agent():
    world = create_world("world2d_lite", seed=42)
    assert isinstance(world, World2DLiteWorld)
    x0 = world.agent_x
    world.apply_action("explore")
    assert world.agent_x != x0
    assert world.distance_traveled > 0


def test_navigation_2d_task_runs():
    result = run_navigation_2d_task(ablation=INTEGRATED_FULL, seed=42, ticks=40)
    assert result.task_id == "navigation_2d"
    assert "distance_traveled" in result.primary_metrics
    assert result.details["world_mode"] == "world2d_lite"


def test_task_registry_includes_navigation_2d():
    assert "navigation_2d" in TASK_REGISTRY


def test_legacy_adapter_wires_brain():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=12, legacy_adapter_mode="integrated")
    )
    assert rt.legacy_brain is not None
    assert rt.config.use_legacy_adapter is True
    rt.run()
    summary = summarize_legacy_adapter(rt)
    assert summary["legacy_adapter_active"] is True


def test_legacy_adapter_export(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=10, legacy_adapter_mode="integrated")
    )
    result = rt.run()
    out = tmp_path / "adapter.json"
    meta = export_legacy_adapter_report(rt, result, out)
    assert meta["exported"] is True
    assert out.exists()


def test_scale_metrics_collect():
    rt = IntegratedRuntime(IntegratedRuntimeConfig(seed=42, ticks=15, scale_mode="integrated"))
    result = rt.run()
    metrics = collect_scale_metrics(rt, result)
    assert metrics["events_per_tick"] > 0
    assert metrics["enabled_processes"] > 0


def test_scale_profile_export(tmp_path: Path):
    rt = IntegratedRuntime(IntegratedRuntimeConfig(seed=42, ticks=12, scale_mode="integrated"))
    result = rt.run()
    meta = export_scale_profile(rt, result, tmp_path / "scale.json", elapsed_seconds=0.5)
    assert meta["exported"] is True
    data = json.loads((tmp_path / "scale.json").read_text(encoding="utf-8"))
    assert "metrics" in data


def test_benchmark_runtime_ticks():
    rt = IntegratedRuntime(IntegratedRuntimeConfig(seed=42, ticks=10))
    payload = benchmark_runtime_ticks(rt, 10)
    assert payload["metrics"]["ticks_per_second"] > 0


def test_hierarchical_inference_summary():
    effects = [
        {"task_id": "survival", "ablation_id": "abl_no_memory", "cohens_d": -0.8},
        {"task_id": "survival", "ablation_id": "abl_no_pfc", "cohens_d": -0.5},
    ]
    summary = summarize_hierarchical_effects(effects)
    assert "memory" in summary["by_layer"]
    assert "executive" in summary["by_layer"]


def test_statistics_hierarchical_export(tmp_path: Path):
    results = [
        {"task_id": "survival", "ablation_id": "integrated_full", "seed": 42,
         "primary_metrics": {"x": 1.0}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "integrated_full", "seed": 99,
         "primary_metrics": {"x": 0.9}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "abl_no_memory", "seed": 42,
         "primary_metrics": {"x": 0.2}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "abl_no_memory", "seed": 99,
         "primary_metrics": {"x": 0.1}, "details": {"lesion_id": "lesion_none"}},
    ]
    payload = export_statistics(
        results, tmp_path / "stats.json",
        include_inference=True,
        include_hierarchical=True,
    )
    assert payload["hierarchical_inference_enabled"] is True
    assert "hierarchical_inference" in payload


def test_integrated_v30_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v30.yaml")
    result = rt.run(20)
    assert result["profile"] == "integrated_v30"
    assert result["legacy_adapter_mode"] == "integrated"
    assert result["world_mode"] == "world2d_lite"
    assert result["scale_mode"] == "integrated"
    assert result["hierarchical_inference_mode"] == "integrated"
