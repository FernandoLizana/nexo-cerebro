"""Tests Sprints 23–26 — legacy bridge, mundo extendido, inferencia y pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.behavioral.inference import enrich_effects_with_inference
from nexo.behavioral.legacy_bridge import compare_integrated_legacy, export_legacy_bridge
from nexo.behavioral.manifest import BatteryManifest
from nexo.behavioral.orchestration import run_integrated_pipeline
from nexo.behavioral.statistics import export_statistics
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import run_foraging_task
from nexo.demo.extended_room import ExtendedRoomWorld
from nexo.demo.world_factory import create_world
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_extended_world_has_seek_shelter():
    world = create_world("extended")
    assert isinstance(world, ExtendedRoomWorld)
    world.weather_level = 0.6
    actions = world.available_actions()
    assert "seek_shelter" in actions


def test_foraging_task_runs():
    result = run_foraging_task(ablation=INTEGRATED_FULL, seed=42, ticks=40)
    assert result.task_id == "foraging"
    assert "shelter_ratio" in result.primary_metrics
    assert result.details["world_mode"] == "extended"


def test_task_registry_includes_foraging():
    assert "foraging" in TASK_REGISTRY


def test_legacy_bridge_compare():
    integrated = {"actions_taken": ["eat", "rest", "explore"], "trajectory_hash": "a"}
    legacy = {"actions": ["eat", "rest", "tv"], "trajectory_hash": "b"}
    cmp = compare_integrated_legacy(integrated, legacy)
    assert cmp["action_overlap_ratio"] > 0.5
    assert cmp["hash_match"] is False


def test_legacy_bridge_export(tmp_path: Path):
    rt = IntegratedRuntime(IntegratedRuntimeConfig(seed=42, ticks=8))
    result = rt.run()
    out = tmp_path / "bridge.json"
    meta = export_legacy_bridge(result, seed=42, ticks=8, output_path=out)
    assert meta["exported"] is True
    assert out.exists()


def test_inference_enriches_effects():
    results = [
        {"task_id": "survival", "ablation_id": "integrated_full", "seed": 42,
         "primary_metrics": {"x": 1.0}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "integrated_full", "seed": 99,
         "primary_metrics": {"x": 0.9}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "abl_no_pfc", "seed": 42,
         "primary_metrics": {"x": 0.2}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "abl_no_pfc", "seed": 99,
         "primary_metrics": {"x": 0.1}, "details": {"lesion_id": "lesion_none"}},
    ]
    effects = [{"task_id": "survival", "ablation_id": "abl_no_pfc", "lesion_id": "lesion_none", "metric": "x"}]
    enriched = enrich_effects_with_inference(results, effects)
    assert "inference_ci_low" in enriched[0]
    assert "inference_ci_high" in enriched[0]


def test_statistics_inference_export(tmp_path: Path):
    results = [
        {"task_id": "survival", "ablation_id": "integrated_full", "seed": 42,
         "primary_metrics": {"x": 1.0}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "integrated_full", "seed": 99,
         "primary_metrics": {"x": 0.9}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "abl_no_pfc", "seed": 42,
         "primary_metrics": {"x": 0.1}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "abl_no_pfc", "seed": 99,
         "primary_metrics": {"x": 0.05}, "details": {"lesion_id": "lesion_none"}},
    ]
    payload = export_statistics(results, tmp_path / "s.json", include_inference=True)
    assert payload["inference_enabled"] is True
    assert any("inference_ci_low" in e for e in payload["effect_sizes"])


def test_pipeline_runs_mini_manifest(tmp_path: Path):
    manifest = _repo_root() / "configs/battery/integrated_v6_mini.yaml"
    out = tmp_path / "pipeline.json"
    summary = run_integrated_pipeline(
        manifest,
        pipeline_output=out,
    )
    assert summary["battery"]["total_runs"] == 2
    assert out.exists()


def test_integrated_v26_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v26.yaml")
    result = rt.run(25)
    assert result["profile"] == "integrated_v26"
    assert result["legacy_bridge_mode"] == "integrated"
    assert result["world_mode"] == "extended"
    assert result["inference_mode"] == "integrated"
    assert result["orchestration_mode"] == "integrated"


def test_manifest_v6_has_inference_and_foraging():
    manifest = BatteryManifest.from_yaml(_repo_root() / "configs/battery/integrated_v6.yaml")
    assert "foraging" in manifest.tasks
    assert manifest.inference_mode == "integrated"
    assert len(manifest.tasks) == 7
