"""Tests Sprint 14 — enrutamiento ampliado y estadística de batería."""

from __future__ import annotations

import json
from pathlib import Path

from nexo.behavioral.manifest import BatteryManifest, execute_manifest
from nexo.behavioral.statistics import (
    aggregate_by_condition,
    bootstrap_ci,
    cohens_d,
    effect_sizes_vs_baseline,
    export_statistics,
)
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_bootstrap_ci_bounds():
    values = [0.2, 0.4, 0.6, 0.8]
    mean, lo, hi = bootstrap_ci(values, n_boot=500, seed=1)
    assert lo <= mean <= hi
    assert hi - lo > 0.0


def test_cohens_d_nonzero_for_different_groups():
    d = cohens_d([1.0, 1.1, 0.9], [0.1, 0.2, 0.0])
    assert d > 0.5


def test_routing_mode_emits_audit_events():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=20,
            memory_mode="integrated",
            consciousness_mode="integrated",
            routing_mode="integrated",
        )
    )
    result = rt.run()
    assert result["routing_mode"] == "integrated"
    assert result["connectome_routing_events"] == 3


def test_routing_lesion_reduces_episodic_gain():
    cfg = IntegratedRuntimeConfig(
        seed=42,
        ticks=55,
        memory_mode="integrated",
        consciousness_mode="integrated",
        executive_mode="integrated",
        routing_mode="integrated",
        intervention_mode="integrated",
    )
    full = IntegratedRuntime(cfg)
    full.run()
    gain_full = float(full.scheduler.config.get("connectome_episodic_route_gain", 0.0))

    lesioned = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=55,
            memory_mode="integrated",
            consciousness_mode="integrated",
            executive_mode="integrated",
            routing_mode="integrated",
            intervention_mode="integrated",
            lesion_profile="lesion_sever_hippo_pfc",
        )
    )
    lesioned.run()
    gain_cut = float(lesioned.scheduler.config.get("connectome_episodic_route_gain", 0.0))
    assert gain_full > 0.0
    assert gain_cut == 0.0


def test_routing_changes_trajectory():
    base = dict(
        seed=42,
        ticks=50,
        memory_mode="integrated",
        consciousness_mode="integrated",
        executive_mode="integrated",
        latency_mode="integrated",
    )
    legacy = IntegratedRuntime(IntegratedRuntimeConfig(**base, routing_mode="legacy")).run()
    routed = IntegratedRuntime(IntegratedRuntimeConfig(**base, routing_mode="integrated")).run()
    assert legacy["trajectory_hash"] != routed["trajectory_hash"]


def test_statistics_export(tmp_path: Path):
    results = [
        {"task_id": "survival", "ablation_id": "integrated_full", "seed": 42,
         "primary_metrics": {"x": 1.0}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "integrated_full", "seed": 99,
         "primary_metrics": {"x": 0.8}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "abl_no_pfc", "seed": 42,
         "primary_metrics": {"x": 0.5}, "details": {"lesion_id": "lesion_none"}},
    ]
    path = tmp_path / "stats.json"
    payload = export_statistics(results, path)
    assert len(payload["aggregates"]) >= 2
    assert len(payload["effect_sizes"]) >= 1
    assert path.exists()


def test_manifest_v2_has_statistics_export():
    manifest = BatteryManifest.from_yaml(_repo_root() / "configs/battery/integrated_v2.yaml")
    assert manifest.statistics_mode == "integrated"
    assert manifest.routing_mode == "integrated"
    assert manifest.export_statistics is not None


def test_execute_manifest_exports_statistics(tmp_path: Path):
    src = _repo_root() / "configs/battery/integrated_v2.yaml"
    custom = tmp_path / "mini.yaml"
    custom.write_text(
        src.read_text(encoding="utf-8")
        .replace("seeds: [42, 99]", "seeds: [42]")
        .replace("results/integrated_battery/", str(tmp_path / "out") + "/"),
        encoding="utf-8",
    )
    summary = execute_manifest(custom)
    assert summary.get("statistics_aggregates", 0) >= 1
    stats_path = tmp_path / "out" / "statistics_v2.json"
    assert stats_path.exists()
    loaded = json.loads(stats_path.read_text(encoding="utf-8"))
    assert "effect_sizes" in loaded


def test_integrated_v14_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v14.yaml")
    result = rt.run(40)
    assert result["profile"] == "integrated_v14"
    assert result["routing_mode"] == "integrated"
    assert result["statistics_mode"] == "integrated"
    assert result["connectome_routing_events"] == 3
