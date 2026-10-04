"""Tests Sprint 13 — análisis comparativo y manifiesto de batería."""

from __future__ import annotations

import json
from pathlib import Path

from nexo.behavioral.comparison import compare_to_baseline, export_comparison, rank_by_effect
from nexo.behavioral.fingerprint import compute_behavior_fingerprint, metric_fingerprint_hash
from nexo.behavioral.manifest import BatteryManifest, execute_manifest
from nexo.behavioral.metrics import compute_metrics
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_fingerprint_hash_stable():
    metrics = {"survival_success": 1.0, "final_energy": 0.5, "action_entropy": 1.2, "eat_ratio": 0.3, "mean_reward": 0.1}
    h1 = metric_fingerprint_hash(metrics)
    h2 = metric_fingerprint_hash(metrics)
    assert h1 == h2
    assert len(h1) == 16


def test_compare_to_baseline_finds_deltas():
    results = [
        {
            "task_id": "survival",
            "ablation_id": "integrated_full",
            "seed": 42,
            "primary_metrics": {"survival_success": 1.0, "final_energy": 0.5},
            "details": {"lesion_id": "lesion_none"},
        },
        {
            "task_id": "survival",
            "ablation_id": "abl_no_executive",
            "seed": 42,
            "primary_metrics": {"survival_success": 0.0, "final_energy": 0.2},
            "details": {"lesion_id": "lesion_none"},
        },
    ]
    entries = compare_to_baseline(results)
    assert len(entries) == 2
    altered = [e for e in entries if e.ablation_id == "abl_no_executive"][0]
    assert altered.deltas["survival_success"] == -1.0
    assert altered.l1_distance > 0.0


def test_rank_by_effect_orders_conditions():
    results = [
        {"task_id": "survival", "ablation_id": "integrated_full", "seed": 42,
         "primary_metrics": {"x": 1.0}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "abl_no_pfc", "seed": 42,
         "primary_metrics": {"x": 0.0}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "integrated_full", "seed": 42,
         "primary_metrics": {"x": 0.5}, "details": {"lesion_id": "lesion_sever_pfc_bg"}},
    ]
    ranked = rank_by_effect(compare_to_baseline(results))
    assert len(ranked) >= 1
    assert ranked[0]["mean_l1_distance"] >= 0.0


def test_analysis_mode_emits_fingerprints():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=45,
            perception_mode="predictive",
            executive_mode="integrated",
            analysis_mode="integrated",
        )
    )
    result = rt.run()
    assert result["analysis_mode"] == "integrated"
    assert result["behavior_fingerprints"] >= 1
    assert len(result["metric_fingerprint"]) == 16


def test_manifest_loads_v2():
    path = _repo_root() / "configs/battery/integrated_v2.yaml"
    manifest = BatteryManifest.from_yaml(path)
    assert manifest.name == "integrated_battery_v2"
    assert "integrated_full" in manifest.ablations
    assert manifest.export_comparison is not None


def test_execute_manifest_subset(tmp_path: Path):
    src = _repo_root() / "configs/battery/integrated_v2.yaml"
    custom = tmp_path / "mini.yaml"
    custom.write_text(
        (src.read_text(encoding="utf-8")).replace(
            "seeds: [42, 99]",
            "seeds: [42]",
        ).replace(
            "results/integrated_battery/",
            str(tmp_path / "out") + "/",
        ),
        encoding="utf-8",
    )
    summary = execute_manifest(custom)
    assert summary["total_runs"] == 18  # 2 ablations × 3 lesions × 1 seed × 3 tasks
    assert summary.get("comparison_entries", 0) >= 18


def test_integrated_v13_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v13.yaml")
    result = rt.run(40)
    assert result["profile"] == "integrated_v13"
    assert result["analysis_mode"] == "integrated"
    assert result["behavior_fingerprints"] >= 1


def test_export_comparison_roundtrip(tmp_path: Path):
    results = [
        {"task_id": "survival", "ablation_id": "integrated_full", "seed": 42,
         "primary_metrics": {"a": 1.0}, "details": {"lesion_id": "lesion_none"}},
        {"task_id": "survival", "ablation_id": "abl_no_pfc", "seed": 42,
         "primary_metrics": {"a": 0.5}, "details": {"lesion_id": "lesion_none"}},
    ]
    path = tmp_path / "cmp.json"
    payload = export_comparison(compare_to_baseline(results), path)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["n_entries"] == payload["n_entries"]
    assert path.exists()
