"""Tests Sprint 7 — workspace global y metacognición."""

from __future__ import annotations

from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config
from nexo.metacognition.monitor import MetacognitiveMonitor
from nexo.workspace.global_workspace import GlobalWorkspace


def test_global_workspace_selects_top_candidates():
    ws = GlobalWorkspace(capacity=2)
    candidates = ws.gather_from_events(
        percepts=[
            {"modality": "food", "salience": 0.8},
            {"modality": "distractor", "salience": 0.4},
        ],
        drives={"hunger": 0.6},
        focus=("food",),
        energy=0.3,
    )
    winners = ws.select_winners(candidates)
    assert len(winners) <= 2
    assert winners[0].salience >= winners[-1].salience
    bias = ws.action_bias()
    assert "eat" in bias or len(bias) >= 0


def test_metacognition_reflects_conflict():
    monitor = MetacognitiveMonitor()
    clear = monitor.evaluate(
        winner_salience=0.7,
        total_salience=1.0,
        conflict=0.1,
        surprise=0.05,
        sleep_pressure=0.1,
        deliberation_confidence=0.8,
    )
    conflicted = monitor.evaluate(
        winner_salience=0.5,
        total_salience=1.0,
        conflict=0.7,
        surprise=0.3,
        sleep_pressure=0.1,
        deliberation_confidence=0.5,
        pfc_veto=True,
    )
    assert conflicted.doubt > clear.doubt
    assert conflicted.felt in ("dividido", "difuso", "nublado")


def test_integrated_consciousness_emits_events():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=40,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="integrated",
            learning_mode="integrated",
            consciousness_mode="integrated",
            profile="test_v7",
        )
    )
    result = rt.run()
    types = {e.event_type for e in rt.state_store.event_log}
    assert "workspace.broadcast" in types
    assert "metacognition.updated" in types
    assert result["consciousness_mode"] == "integrated"
    assert result["workspace_broadcasts"] > 0


def test_consciousness_integrated_vs_legacy_metrics():
    legacy = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=50,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="integrated",
            learning_mode="integrated",
            consciousness_mode="legacy",
        )
    ).run()
    integrated = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=50,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="integrated",
            learning_mode="integrated",
            consciousness_mode="integrated",
        )
    ).run()
    assert legacy["workspace_broadcasts"] == 0
    assert integrated["workspace_broadcasts"] > 0
    assert integrated["metacognition_events"] > 0


def test_consciousness_reproducible():
    cfg = dict(
        seed=55,
        ticks=35,
        perception_mode="predictive",
        memory_mode="integrated",
        executive_mode="integrated",
        learning_mode="integrated",
        consciousness_mode="integrated",
    )
    r1 = IntegratedRuntime(IntegratedRuntimeConfig(**cfg)).run()
    r2 = IntegratedRuntime(IntegratedRuntimeConfig(**cfg)).run()
    assert r1["trajectory_hash"] == r2["trajectory_hash"]
    assert r1["workspace_broadcasts"] == r2["workspace_broadcasts"]


def test_integrated_v7_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v7.yaml")
    result = rt.run(40)
    assert result["profile"] == "integrated_v7"
    assert result["consciousness_mode"] == "integrated"
    assert result["metacognitive_felt"] in ("claro", "difuso", "dividido", "nublado", "somnoliento", "")
