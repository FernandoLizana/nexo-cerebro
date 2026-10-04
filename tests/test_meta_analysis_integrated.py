"""Tests Sprint 18 — meta-análisis entre réplicas y curiosity_explore."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.behavioral.event_log import summarize_event_log_payload
from nexo.behavioral.manifest import BatteryManifest
from nexo.behavioral.meta_analysis import (
    build_meta_analysis,
    discover_replication_bundles,
    export_meta_analysis,
    load_replication_bundle,
)
from nexo.behavioral.replication import build_replication_bundle
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import run_curiosity_explore_task
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def _make_bundle(tmp_path: Path, seed: int, profile: str = "test_meta") -> Path:
    bundle_dir = tmp_path / f"seed_{seed}"
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=seed,
            ticks=18,
            profile=profile,
            tracing_mode="integrated",
            replication_mode="integrated",
            eventlog_mode="integrated",
        )
    )
    result = rt.run()
    build_replication_bundle(rt, result, bundle_dir)
    return bundle_dir


def test_event_log_summary_counts_types():
    payload = {
        "events": [
            {"tick": 1, "type": "action.selected", "source": "motor"},
            {"tick": 2, "type": "action.selected", "source": "motor"},
            {"tick": 3, "type": "memory.encoded", "source": "hippo"},
        ]
    }
    summary = summarize_event_log_payload(payload)
    assert summary["n_events"] == 3
    assert summary["type_counts"]["action.selected"] == 2
    assert summary["tick_min"] == 1
    assert summary["tick_max"] == 3


def test_load_and_discover_replication_bundles(tmp_path: Path):
    _make_bundle(tmp_path / "replications", 42)
    _make_bundle(tmp_path / "replications", 99)
    bundles = discover_replication_bundles(tmp_path / "replications")
    assert len(bundles) == 2
    loaded = load_replication_bundle(Path(bundles[0]["dir"]))
    assert loaded is not None
    assert loaded["manifest"]["seed"] in (42, 99)


def test_meta_analysis_detects_divergent_trajectories(tmp_path: Path):
    root = tmp_path / "replications"
    _make_bundle(root, 42)
    _make_bundle(root, 99)
    bundles = discover_replication_bundles(root)
    payload = build_meta_analysis(bundles, replication_root=str(root))
    assert payload["n_bundles"] == 2
    assert payload["summary"]["unique_trajectory_hashes"] >= 1
    assert "final_energy" in payload["aggregates"]


def test_export_meta_analysis_writes_json(tmp_path: Path):
    root = tmp_path / "replications"
    _make_bundle(root, 42)
    out = tmp_path / "meta.json"
    meta = export_meta_analysis(root, out)
    assert meta["exported"] is True
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["n_bundles"] == 1


def test_curiosity_explore_task_runs():
    result = run_curiosity_explore_task(ablation=INTEGRATED_FULL, seed=42, ticks=45)
    assert result.task_id == "curiosity_explore"
    assert "explore_ratio" in result.primary_metrics
    assert "curiosity_score" in result.primary_metrics
    assert result.details["danger_level"] == 0.05


def test_task_registry_includes_curiosity_explore():
    assert "curiosity_explore" in TASK_REGISTRY


def test_integrated_v18_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v18.yaml")
    result = rt.run(35)
    assert result["profile"] == "integrated_v18"
    assert result["meta_analysis_mode"] == "integrated"


def test_manifest_v4_lists_curiosity_explore():
    manifest = BatteryManifest.from_yaml(_repo_root() / "configs/battery/integrated_v4.yaml")
    assert "curiosity_explore" in manifest.tasks
    assert len(manifest.tasks) == 5


def test_runtime_export_meta_analysis(tmp_path: Path):
    repl_root = tmp_path / "replications"
    _make_bundle(repl_root, 42)
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=10, meta_analysis_mode="integrated")
    )
    out = tmp_path / "summary.json"
    meta = rt.export_meta_analysis(repl_root, out)
    assert meta["exported"] is True
    assert out.exists()
