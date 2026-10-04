"""Tests Sprints 19–22 — batch, cross-batería, fenomenología y social_approach."""

from __future__ import annotations

import json
from pathlib import Path

from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.behavioral.cross_battery import compare_battery_reports, export_cross_battery
from nexo.behavioral.phenomenology import build_phenomenology_timeline, export_phenomenology
from nexo.behavioral.replication import build_replication_bundle
from nexo.behavioral.replication_batch import run_replication_batch_from_config
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import run_social_approach_task
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def _sample_battery_rows(task_id: str, metric: str, val_a: float, val_b: float) -> dict[str, list]:
    base = {
        "task_id": task_id,
        "ablation_id": "integrated_full",
        "seed": 42,
        "details": {"lesion_id": "lesion_none"},
    }
    return {
        "v3": [{**base, "primary_metrics": {metric: val_a}}],
        "v4": [{**base, "primary_metrics": {metric: val_b}}],
    }


def test_replication_batch_writes_seed_dirs(tmp_path: Path):
    cfg = IntegratedRuntimeConfig(
        seed=42,
        ticks=12,
        replication_mode="integrated",
        tracing_mode="integrated",
        profile="batch_test",
    )
    summary = run_replication_batch_from_config(cfg, (42, 99), tmp_path / "batch", ticks=12)
    assert summary["n_seeds"] == 2
    assert (tmp_path / "batch" / "seed_42" / "manifest.json").exists()
    assert (tmp_path / "batch" / "seed_99" / "manifest.json").exists()
    assert (tmp_path / "batch" / "batch_summary.json").exists()


def test_cross_battery_detects_delta(tmp_path: Path):
    labeled = _sample_battery_rows("survival", "survival_success", 1.0, 0.5)
    payload = compare_battery_reports(labeled)
    assert payload["n_comparisons"] == 1
    delta = payload["comparisons"][0]["deltas_vs_base"]["v4"]
    assert delta == -0.5


def test_export_cross_battery(tmp_path: Path):
    v3 = tmp_path / "v3.json"
    v4 = tmp_path / "v4.json"
    v3.write_text(json.dumps(_sample_battery_rows("survival", "x", 1.0, 0.5)["v3"]), encoding="utf-8")
    v4.write_text(json.dumps(_sample_battery_rows("survival", "x", 1.0, 0.5)["v4"]), encoding="utf-8")
    out = tmp_path / "cmp.json"
    meta = export_cross_battery({"v3": v3, "v4": v4}, out)
    assert meta["exported"] is True
    assert out.exists()


def test_phenomenology_timeline_segments():
    events = [
        {"tick": 1, "type": "action.selected", "payload": {"action": "explore"}},
        {"tick": 2, "type": "language.produced", "payload": {"text": "hola"}},
        {"tick": 20, "type": "metacognition.updated", "payload": {"felt": "claro"}},
    ]
    timeline = build_phenomenology_timeline(events, window_ticks=10)
    assert timeline["salient_events"] == 3
    assert timeline["n_segments"] >= 2


def test_phenomenology_export(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=20, phenomenology_mode="integrated")
    )
    rt.run()
    meta = export_phenomenology(rt, tmp_path / "phenom.json")
    assert meta["exported"] is True
    data = json.loads((tmp_path / "phenom.json").read_text(encoding="utf-8"))
    assert "timeline" in data


def test_replication_includes_phenomenology(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=15,
            replication_mode="integrated",
            phenomenology_mode="integrated",
            tracing_mode="integrated",
        )
    )
    result = rt.run()
    build_replication_bundle(rt, result, tmp_path / "bundle")
    assert (tmp_path / "bundle" / "phenomenology.json").exists()


def test_social_approach_task_runs():
    result = run_social_approach_task(ablation=INTEGRATED_FULL, seed=42, ticks=45)
    assert result.task_id == "social_approach"
    assert "approach_ratio" in result.primary_metrics
    assert "social_score" in result.primary_metrics


def test_task_registry_includes_social_approach():
    assert "social_approach" in TASK_REGISTRY


def test_integrated_v22_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v22.yaml")
    result = rt.run(30)
    assert result["profile"] == "integrated_v22"
    assert result["replication_batch_mode"] == "integrated"
    assert result["cross_battery_mode"] == "integrated"
    assert result["phenomenology_mode"] == "integrated"


def test_runtime_export_replication_batch(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=10,
            replication_mode="integrated",
            replication_batch_mode="integrated",
            tracing_mode="integrated",
        )
    )
    meta = rt.export_replication_batch((42, 99), tmp_path / "batch", ticks=10)
    assert meta["n_seeds"] == 2
