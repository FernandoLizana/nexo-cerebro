"""Tests Sprints 31–34 — deliberación, legacy actions, LIF scale, publicación."""

from __future__ import annotations

import json
from pathlib import Path

from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.behavioral.deliberation_bridge import export_deliberation_bridge, summarize_deliberation_bridge
from nexo.behavioral.lif_scale import export_lif_scale_probe, probe_lif_scale_availability
from nexo.behavioral.publication import export_publication_bundle
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import run_legacy_navigation_task
from nexo.demo.world2d_actions import map_legacy_action
from nexo.demo.world2d_lite import World2DLiteWorld
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_map_legacy_action():
    assert map_legacy_action("tv") == "inspect_distractor"
    assert map_legacy_action("research") == "explore"
    assert map_legacy_action("eat") == "eat"


def test_world2d_legacy_actions_enabled():
    world = World2DLiteWorld(seed=42, legacy_actions_enabled=True)
    world.apply_action("tv")
    assert world.action_history[-1] == "inspect_distractor"


def test_legacy_navigation_task_runs():
    result = run_legacy_navigation_task(ablation=INTEGRATED_FULL, seed=42, ticks=35)
    assert result.task_id == "legacy_navigation"
    assert result.primary_metrics["mapping_coverage"] == 1.0


def test_task_registry_includes_legacy_navigation():
    assert "legacy_navigation" in TASK_REGISTRY


def test_deliberation_bridge_audit_process():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=12,
            deliberation_bridge_mode="integrated",
            legacy_adapter_mode="integrated",
        )
    )
    rt.run()
    summary = summarize_deliberation_bridge(rt)
    assert summary["authority"] == "integrated"


def test_deliberation_bridge_export(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=10,
            deliberation_bridge_mode="integrated",
            legacy_adapter_mode="integrated",
        )
    )
    result = rt.run()
    out = tmp_path / "bridge.json"
    meta = export_deliberation_bridge(rt, result, out)
    assert meta["exported"] is True
    assert out.exists()


def test_lif_scale_probe_availability():
    probe = probe_lif_scale_availability()
    assert "available" in probe


def test_lif_scale_export_without_bench(tmp_path: Path):
    meta = export_lif_scale_probe(tmp_path / "lif.json", run_bench=False)
    assert meta["exported"] is True


def test_publication_bundle_export(tmp_path: Path):
    rt = IntegratedRuntime(IntegratedRuntimeConfig(seed=42, ticks=12, publication_mode="integrated"))
    result = rt.run()
    out_dir = tmp_path / "pub"
    meta = export_publication_bundle(rt, result, out_dir)
    assert meta["exported"] is True
    assert (out_dir / "publication_manifest.json").exists()
    assert (out_dir / "result.json").exists()
    manifest = json.loads((out_dir / "publication_manifest.json").read_text(encoding="utf-8"))
    assert "config_fingerprint" in manifest


def test_integrated_v34_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v34.yaml")
    result = rt.run(18)
    assert result["profile"] == "integrated_v34"
    assert result["deliberation_bridge_mode"] == "integrated"
    assert result["world2d_legacy_actions_mode"] == "integrated"
    assert result["lif_scale_mode"] == "integrated"
    assert result["publication_mode"] == "integrated"
