"""Tests Sprints 35–38 — fusión deliberación, World2D full, GPU bench CI, paper pack."""

from __future__ import annotations

import json
from pathlib import Path

from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.behavioral.deliberation_fusion import export_deliberation_fusion, summarize_deliberation_fusion
from nexo.behavioral.gpu_bench import export_gpu_bench, run_gpu_bench_ci
from nexo.behavioral.paper_pack import export_paper_pack
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import run_world2d_full_navigation_task
from nexo.demo.world2d_actions import FULL_LEGACY_CATALOG, full_catalog_coverage, map_legacy_action
from nexo.demo.world2d_lite import World2DLiteWorld
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig


def test_full_legacy_action_mapping():
    assert map_legacy_action("clinical", full=True) == "explore"
    assert map_legacy_action("hygiene", full=True) == "rest"
    assert full_catalog_coverage() >= 0.9


def test_world2d_full_actions_enabled():
    world = World2DLiteWorld(seed=42, full_actions_enabled=True)
    world.apply_action("clinical")
    assert world.action_history[-1] == "explore"
    assert "flee" in world.available_actions()


def test_world2d_full_navigation_task_runs():
    result = run_world2d_full_navigation_task(ablation=INTEGRATED_FULL, seed=42, ticks=35)
    assert result.task_id == "world2d_full_navigation"
    assert result.primary_metrics["full_catalog_coverage"] >= 0.9


def test_task_registry_includes_world2d_full_navigation():
    assert "world2d_full_navigation" in TASK_REGISTRY
    assert len(FULL_LEGACY_CATALOG) >= len(("tv", "research", "eat", "wander"))


def test_deliberation_fusion_process():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=12,
            deliberation_bridge_mode="integrated",
            deliberation_fusion_mode="integrated",
            legacy_adapter_mode="integrated",
        )
    )
    rt.run()
    summary = summarize_deliberation_fusion(rt)
    assert summary["fusion_policy"] == "integrated_wins"
    assert summary["authority"] == "integrated"


def test_deliberation_fusion_export(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=10,
            deliberation_bridge_mode="integrated",
            deliberation_fusion_mode="integrated",
            legacy_adapter_mode="integrated",
        )
    )
    result = rt.run()
    out = tmp_path / "fusion.json"
    meta = export_deliberation_fusion(rt, result, out)
    assert meta["exported"] is True
    assert out.exists()


def test_gpu_bench_ci_safe():
    row = run_gpu_bench_ci(profile_key="compact", ticks=1)
    assert "skipped" in row


def test_gpu_bench_export(tmp_path: Path):
    meta = export_gpu_bench(tmp_path / "gpu.json", ci_safe=True)
    assert meta["exported"] is True
    assert (tmp_path / "gpu.json").exists()


def test_paper_pack_export(tmp_path: Path):
    rt = IntegratedRuntime(IntegratedRuntimeConfig(seed=42, ticks=8, paper_pack_mode="integrated"))
    result = rt.run()
    meta = export_paper_pack(rt, result, tmp_path / "paper")
    assert meta["exported"] is True
    assert (tmp_path / "paper" / "metrics.csv").exists()
    assert (tmp_path / "paper" / "metrics_table.tex").exists()
    manifest = json.loads((tmp_path / "paper" / "paper_pack_manifest.json").read_text(encoding="utf-8"))
    assert manifest["profile"] == result["profile"]
