"""Tests Sprint 17 — safety_escape, FDR y event_log."""

from __future__ import annotations

import json
from pathlib import Path

from nexo.behavioral.correction import apply_fdr_to_effects, benjamini_hochberg_fdr
from nexo.behavioral.event_log import export_event_log
from nexo.behavioral.manifest import BatteryManifest, execute_manifest
from nexo.behavioral.replication import build_replication_bundle
from nexo.behavioral.statistics import export_statistics
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import run_safety_escape_task
from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_safety_escape_task_runs():
    result = run_safety_escape_task(ablation=INTEGRATED_FULL, seed=42, ticks=45)
    assert result.task_id == "safety_escape"
    assert "flee_ratio" in result.primary_metrics
    assert result.details["danger_level"] == 0.85


def test_task_registry_includes_safety_escape():
    assert "safety_escape" in TASK_REGISTRY


def test_fdr_correction_orders_q_values():
    q = benjamini_hochberg_fdr([0.01, 0.04, 0.03, 0.20])
    assert q[0] <= q[3]
    assert all(0.0 <= v <= 1.0 for v in q)


def test_apply_fdr_to_effects():
    effects = [
        {"metric": "a", "permutation_p": 0.01},
        {"metric": "b", "permutation_p": 0.15},
        {"metric": "c", "permutation_p": 0.04},
    ]
    corrected = apply_fdr_to_effects(effects)
    assert all("permutation_q" in e for e in corrected if "permutation_p" in e)
    assert corrected[0]["significant_fdr_05"] is True


def test_statistics_fdr_export(tmp_path: Path):
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
    payload = export_statistics(
        results, tmp_path / "s.json",
        include_permutation=True,
        include_fdr_correction=True,
    )
    assert payload["fdr_correction_enabled"] is True
    assert any("permutation_q" in e for e in payload["effect_sizes"])


def test_event_log_export(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=15, eventlog_mode="integrated")
    )
    rt.run()
    meta = export_event_log(rt, tmp_path / "events.json")
    assert meta["exported"] is True
    assert meta["n_events"] > 0
    data = json.loads((tmp_path / "events.json").read_text(encoding="utf-8"))
    assert "events" in data


def test_replication_includes_event_log(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=15,
            tracing_mode="integrated",
            replication_mode="integrated",
            eventlog_mode="integrated",
        )
    )
    result = rt.run()
    build_replication_bundle(rt, result, tmp_path / "bundle")
    assert (tmp_path / "bundle" / "event_log.json").exists()


def test_integrated_v17_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v17.yaml")
    result = rt.run(35)
    assert result["profile"] == "integrated_v17"
    assert result["correction_mode"] == "integrated"
    assert result["eventlog_mode"] == "integrated"


def test_manifest_v3_lists_safety_escape():
    manifest = BatteryManifest.from_yaml(_repo_root() / "configs/battery/integrated_v3.yaml")
    assert "safety_escape" in manifest.tasks
    assert manifest.correction_mode == "integrated"
