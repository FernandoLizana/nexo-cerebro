"""Tests Sprints 51–54 — adapter temprano, World2D headless, puente roadmap100."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.behavioral.legacy_adapter_early import export_legacy_adapter_early, summarize_legacy_adapter_early
from nexo.behavioral.roadmap100_bridge import export_roadmap100_bridge, summarize_roadmap100_bridge
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import (
    run_legacy_adapter_timing_task,
    run_roadmap100_bridge_smoke_task,
    run_world2d_headless_navigation_task,
)
from nexo.core.process_legacy_early import LegacyEarlyBrainAdapterProcess
from nexo.core.process_roadmap100_bridge import Roadmap100BridgeProcess
from nexo.demo.world2d_headless import World2DHeadlessWorld
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_legacy_early_process_priority():
    proc = LegacyEarlyBrainAdapterProcess()
    assert proc.priority == 61
    assert proc.process_id == "legacy_brain_adapter_early"


def test_world2d_headless_world():
    world = World2DHeadlessWorld(seed=42, headless_enabled=True)
    assert world.furniture_count >= 8
    world.apply_action("explore")
    assert world.headless_steps >= 0
    assert world.headless_fidelity_score() > 0.0


@pytest.mark.slow
def test_legacy_adapter_timing_task():
    result = run_legacy_adapter_timing_task(ablation=INTEGRATED_FULL, seed=42, ticks=12)
    assert result.task_id == "legacy_adapter_timing"
    assert result.primary_metrics["timing_score"] >= 0.0


@pytest.mark.slow
def test_world2d_headless_navigation_task():
    result = run_world2d_headless_navigation_task(ablation=INTEGRATED_FULL, seed=42, ticks=12)
    assert result.task_id == "world2d_headless_navigation"
    assert result.primary_metrics["headless_fidelity"] > 0.0


@pytest.mark.slow
def test_roadmap100_bridge_smoke_task():
    result = run_roadmap100_bridge_smoke_task(ablation=INTEGRATED_FULL, seed=42, ticks=12)
    assert result.task_id == "roadmap100_bridge_smoke"
    assert result.primary_metrics["roadmap100_coverage"] >= 0.0
    assert result.primary_metrics["bridge_events"] >= 0.0


def test_task_registry_fase9():
    for task_id in (
        "legacy_adapter_timing",
        "world2d_headless_navigation",
        "roadmap100_bridge_smoke",
    ):
        assert task_id in TASK_REGISTRY


@pytest.mark.slow
def test_runtime_legacy_adapter_early_export(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=10,
            legacy_adapter_mode="integrated",
            legacy_adapter_early_mode="integrated",
        )
    )
    result = rt.run()
    meta = rt.export_legacy_adapter_early(result, tmp_path / "early.json")
    assert meta["exported"] is True
    summary = summarize_legacy_adapter_early(rt)
    assert summary["early_adapter"] is True
    assert summary["legacy_adapter_priority"] == 61


@pytest.mark.slow
def test_runtime_roadmap100_bridge_export(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=10,
            legacy_adapter_mode="integrated",
            roadmap100_bridge_mode="integrated",
        )
    )
    result = rt.run()
    meta = rt.export_roadmap100_bridge(result, tmp_path / "bridge.json")
    assert meta["exported"] is True
    summary = summarize_roadmap100_bridge(rt)
    assert summary["bridge_mode"] == "advisory"
    assert summary["bridge_events"] >= 0


def test_roadmap100_bridge_process():
    proc = Roadmap100BridgeProcess()
    assert proc.process_id == "roadmap100_bridge"
    assert proc.period_ticks == 5


@pytest.mark.slow
def test_integrated_v54_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v54.yaml")
    result = rt.run(ticks=8)
    assert result["profile"] == "integrated_v54"
    assert result["legacy_adapter_early_mode"] == "integrated"
    assert result["world2d_headless_mode"] == "integrated"
    assert result["roadmap100_bridge_mode"] == "integrated"


@pytest.mark.slow
def test_integrated_v54_yaml_exports(tmp_path: Path, monkeypatch):
    cfg = _repo_root() / "configs/nexo/integrated_v54.yaml"
    import yaml

    data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    data["legacy_adapter_early"]["export_path"] = str(tmp_path / "early.json")
    data["roadmap100_bridge"]["export_path"] = str(tmp_path / "bridge.json")
    data["gpu_bench"]["run_bench"] = False
    patched = tmp_path / "v54.yaml"
    patched.write_text(yaml.dump(data), encoding="utf-8")

    rt = runtime_from_config(patched)
    result = rt.run(ticks=8)
    early = rt.export_legacy_adapter_early(result, tmp_path / "early.json")
    bridge = rt.export_roadmap100_bridge(result, tmp_path / "bridge.json")
    assert early["exported"] is True
    assert bridge["exported"] is True
    payload = json.loads((tmp_path / "bridge.json").read_text(encoding="utf-8"))
    assert "summary" in payload
