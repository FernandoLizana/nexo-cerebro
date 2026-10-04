"""Tests Sprint 15 — trazabilidad integrada y WM→PFC."""

from __future__ import annotations

import json
from pathlib import Path

from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config
from nexo.telemetry.integrated_trace import IntegratedTraceCollector


def test_tracing_mode_emits_trace_events():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=30,
            memory_mode="integrated",
            routing_mode="integrated",
            tracing_mode="integrated",
        )
    )
    result = rt.run()
    assert result["tracing_mode"] == "integrated"
    assert result["trace_events"] == 30
    assert result["trace_summary"]["ticks"] == 30


def test_tracing_legacy_skips_collector():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=10, tracing_mode="legacy")
    )
    result = rt.run()
    assert result["trace_events"] == 0
    assert result["trace_summary"] == {}


def test_export_trace_writes_json(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=25,
            memory_mode="integrated",
            tracing_mode="integrated",
        )
    )
    rt.run()
    out = tmp_path / "trace.json"
    meta = rt.export_trace(out)
    assert meta["exported"] is True
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["ticks"] == 25
    assert len(payload["entries"]) == 25


def test_wm_routing_sets_gain_in_events():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=40,
            memory_mode="integrated",
            routing_mode="integrated",
        )
    )
    rt.run()
    wm_gain = float(rt.scheduler.config.get("connectome_wm_route_gain", 0.0))
    wm_events = [
        e for e in rt.state_store.event_log if e.event_type == "working_memory.updated"
    ]
    assert wm_gain > 0.0
    assert any(e.payload.get("connectome_routed") for e in wm_events)


def test_trace_collector_summary():
    c = IntegratedTraceCollector()
    c.record_tick(tick=1, action="eat", energy=0.5, deliveries=2, config={"connectome_wm_route_gain": 0.8})
    c.record_tick(tick=2, action="rest", energy=0.4, deliveries=0, config={})
    s = c.summary()
    assert s["ticks"] == 2
    assert s["total_deliveries"] == 2
    assert s["ticks_with_wm_gain"] == 1


def test_integrated_v15_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v15.yaml")
    result = rt.run(40)
    assert result["profile"] == "integrated_v15"
    assert result["tracing_mode"] == "integrated"
    assert result["trace_events"] == 40
    assert result["trace_summary"]["ticks"] == 40
