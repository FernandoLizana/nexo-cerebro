"""Tests Sprint 12 — latencia connectome y batería con lesiones."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from nexo.behavioral.benchmark import export_benchmark, summarize_battery
from nexo.connectome.graph import ConnectomeGraph
from nexo.connectome.routing import ConnectomeRouter
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config
from nexo.interventions.profiles import apply_lesion_profile


def _repo_connectome():
    return _repo_root() / "configs/connectome/connectome_v1.yaml"


def test_latency_buffer_defers_then_delivers():
    graph = ConnectomeGraph.from_yaml(_repo_connectome())
    router = ConnectomeRouter(graph=graph, latency_enabled=True)
    signal = np.array([1.0, 0.5, 0.2])
    router.current_tick = 0
    immediate = router.route("prefrontal", "basal_ganglia", signal, 1.0)
    assert np.allclose(immediate, 0.0)
    deliveries: list = []
    for tick in range(1, 4):
        deliveries = router.advance_tick(tick)
    assert any(s == "prefrontal" and t == "basal_ganglia" for s, t, _ in deliveries)
    delivered = router.latency_buffer.get_delivered("prefrontal", "basal_ganglia")
    assert delivered is not None
    assert float(np.linalg.norm(delivered)) > 0.0


def test_latency_legacy_ignores_edge_delay():
    graph = ConnectomeGraph.from_yaml(_repo_connectome())
    router = ConnectomeRouter(graph=graph, latency_enabled=False)
    signal = np.array([1.0, 0.5, 0.2])
    routed = router.route("prefrontal", "basal_ganglia", signal, 1.0)
    assert float(np.linalg.norm(routed)) > 0.0


def test_lesion_delay_adds_latency_ticks():
    graph = ConnectomeGraph.from_yaml(_repo_connectome())
    router = ConnectomeRouter(graph=graph, latency_enabled=True)
    apply_lesion_profile("lesion_delay_pfc_bg", router.lesions)
    signal = np.array([1.0, 0.3, 0.1])
    router.current_tick = 0
    router.route("prefrontal", "basal_ganglia", signal, 1.0)
    # base latency 3 + lesion add 5 => deliver at tick 8
    for tick in range(1, 8):
        assert not router.advance_tick(tick)
    deliveries = router.advance_tick(8)
    assert len(deliveries) >= 1


def test_latency_mode_emits_delivery_events():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=25,
            perception_mode="predictive",
            executive_mode="integrated",
            latency_mode="integrated",
        )
    )
    result = rt.run()
    assert result["latency_mode"] == "integrated"
    assert result["connectome_signals_delivered"] >= 1
    assert result["connectome_delivery_events"] >= 1


def test_latency_changes_trajectory_vs_legacy():
    base = dict(
        seed=42,
        ticks=50,
        perception_mode="predictive",
        memory_mode="integrated",
        executive_mode="integrated",
        intervention_mode="integrated",
        lesion_profile="lesion_delay_pfc_bg",
    )
    legacy = IntegratedRuntime(IntegratedRuntimeConfig(**base, latency_mode="legacy")).run()
    buffered = IntegratedRuntime(IntegratedRuntimeConfig(**base, latency_mode="integrated")).run()
    assert legacy["trajectory_hash"] != buffered["trajectory_hash"]


def test_battery_with_lesions_subset():
    from experiments.integrated_battery.run_battery import run_integrated_battery

    results = run_integrated_battery(
        seeds=(42,),
        ablation_ids=("integrated_full",),
        lesion_ids=("lesion_none", "lesion_sever_pfc_bg"),
        latency_mode="integrated",
    )
    assert len(results) == 6
    lesion_ids = {r["details"]["lesion_id"] for r in results}
    assert lesion_ids == {"lesion_none", "lesion_sever_pfc_bg"}


def test_benchmark_export(tmp_path: Path):
    from experiments.integrated_battery.run_battery import run_integrated_battery

    results = run_integrated_battery(
        seeds=(42,),
        ablation_ids=("integrated_full",),
        lesion_ids=("lesion_none",),
    )
    json_path = tmp_path / "bench.json"
    csv_path = tmp_path / "bench.csv"
    summary = export_benchmark(results, json_path, csv_path=csv_path)
    assert summary["total_runs"] == 3
    assert json_path.exists()
    assert csv_path.exists()
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert "aggregates" in payload["summary"]


def test_integrated_v12_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v12.yaml")
    result = rt.run(40)
    assert result["profile"] == "integrated_v12"
    assert result["latency_mode"] == "integrated"
    assert result["connectome_signals_delivered"] >= 1
