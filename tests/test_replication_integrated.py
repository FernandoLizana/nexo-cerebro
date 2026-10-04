"""Tests Sprint 16 — replicación, permutación y CLI trace."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from nexo.behavioral.permutation import permutation_p_value
from nexo.behavioral.replication import build_replication_bundle, config_fingerprint
from nexo.behavioral.statistics import export_statistics
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_permutation_detects_large_shift():
    base = [1.0, 1.1, 0.9, 1.05]
    cand = [0.1, 0.2, 0.0, 0.15]
    p = permutation_p_value(base, cand, n_perm=500, seed=1)
    assert p < 0.05


def test_permutation_insignificant_for_similar():
    base = [0.5, 0.51, 0.49]
    cand = [0.52, 0.48, 0.5]
    p = permutation_p_value(base, cand, n_perm=300, seed=2)
    assert p > 0.05


def test_statistics_includes_permutation_p(tmp_path: Path):
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
    path = tmp_path / "stats.json"
    payload = export_statistics(results, path, include_permutation=True)
    assert payload["permutation_enabled"] is True
    assert any("permutation_p" in e for e in payload["effect_sizes"])


def test_replication_bundle_writes_files(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=20,
            tracing_mode="integrated",
            replication_mode="integrated",
            profile="test_repl",
        )
    )
    result = rt.run()
    meta = build_replication_bundle(rt, result, tmp_path / "bundle")
    assert (tmp_path / "bundle" / "result.json").exists()
    assert (tmp_path / "bundle" / "manifest.json").exists()
    assert (tmp_path / "bundle" / "config.yaml").exists()
    assert meta["replication_id"] == config_fingerprint(rt.config)


def test_integrated_v16_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v16.yaml")
    result = rt.run(35)
    assert result["profile"] == "integrated_v16"
    assert result["replication_mode"] == "integrated"
    assert result["permutation_mode"] == "integrated"
    assert len(result["replication_id"]) == 16


def test_cli_trace_output(tmp_path: Path):
    trace_path = tmp_path / "cli_trace.json"
    proc = subprocess.run(
        [
            sys.executable, "-m", "nexo.run",
            "--config", str(_repo_root() / "configs/nexo/integrated_v16.yaml"),
            "--ticks", "15",
            "--trace-output", str(trace_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(_repo_root()),
    )
    assert proc.returncode == 0
    assert trace_path.exists()
    out = json.loads(proc.stdout)
    assert out.get("trace_export", {}).get("exported") is True
