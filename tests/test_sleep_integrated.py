"""Tests Sprint 9 — sueño, consolidación y desarrollo."""

from __future__ import annotations

from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config
from nexo.memory.hippocampus.episode import EpisodicMemory
from nexo.memory.hippocampus.store import HippocampalStore
from nexo.memory.consolidation import MemoryConsolidator
from nexo.sleep.architecture import SleepArchitecture
from nexo.development.tracker import DevelopmentTracker, DevelopmentStage


def test_sleep_architecture_enters_nrem():
    arch = SleepArchitecture()
    phase = arch.update(sleep_pressure=0.5, alertness=0.4, tick=10, fatigue=0.3)
    assert phase in ("nrem_light", "nrem_deep", "rem")
    assert arch.is_sleeping


def test_hippocampal_replay_samples_episodes():
    store = HippocampalStore()
    import numpy as np

    rng = np.random.default_rng(1)
    store.encode(
        EpisodicMemory(
            episode_id="e1",
            event_embedding=(0.5, 0.2, 0.1),
            spatial_context=(0.1, 0.2),
            temporal_context=(1.0, 0.0),
            body_context=(0.8, 0.1, 0.0),
            affective_context=(0.0, 0.2, 0.0),
            action="eat",
            outcome="reward=0.5",
            confidence=0.6,
            source_identity="self",
            tick=1,
        ),
        rng=rng,
    )
    samples = store.sample_for_replay(rng=rng, n=1)
    assert len(samples) == 1


def test_consolidator_boosts_confidence():
    consolidator = MemoryConsolidator()
    ep = EpisodicMemory(
        episode_id="e2",
        event_embedding=(0.1, 0.2, 0.3),
        spatial_context=(0.0, 0.0),
        temporal_context=(0.0, 0.0),
        body_context=(0.5, 0.0, 0.0),
        affective_context=(0.0, 0.0, 0.0),
        action="rest",
        outcome="ok",
        confidence=0.5,
        source_identity="self",
        tick=2,
    )
    out = consolidator.consolidate(ep)
    assert out.confidence > ep.confidence


def test_development_advances_with_consolidation():
    dev = DevelopmentTracker()
    for _ in range(8):
        dev.register_consolidation()
    assert dev.stage in (DevelopmentStage.JUVENILE, DevelopmentStage.MATURE)
    assert dev.maturation > 0.2


def test_integrated_sleep_emits_events():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=60,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="integrated",
            learning_mode="integrated",
            consciousness_mode="integrated",
            social_mode="integrated",
            sleep_mode="integrated",
            profile="test_v9",
        )
    )
    rt.body.sleep_pressure = 0.55
    rt.body.fatigue = 0.45
    store: HippocampalStore = rt.scheduler.config["hippocampal_store"]
    import numpy as np

    rng = np.random.default_rng(42)
    for i in range(3):
        store.encode(
            EpisodicMemory(
                episode_id=f"ep{i}",
                event_embedding=(float(i), 0.1, 0.2),
                spatial_context=(0.1, 0.2),
                temporal_context=(float(i), 0.0),
                body_context=(0.7, 0.1, 0.0),
                affective_context=(0.1, 0.2, 0.0),
                action="eat",
                outcome="r",
                confidence=0.55,
                source_identity="self",
                tick=i,
            ),
            rng=rng,
        )
    result = rt.run()
    types = {e.event_type for e in rt.state_store.event_log}
    assert "sleep.phase_changed" in types or result["sleep_phase"] != "awake"
    assert result["sleep_mode"] == "integrated"


def test_sleep_integrated_vs_legacy_metrics():
    cfg_base = dict(
        seed=42,
        ticks=70,
        perception_mode="predictive",
        memory_mode="integrated",
        executive_mode="integrated",
        learning_mode="integrated",
        consciousness_mode="integrated",
        social_mode="integrated",
    )
    legacy = IntegratedRuntime(IntegratedRuntimeConfig(**cfg_base, sleep_mode="legacy")).run()
    rt = IntegratedRuntime(IntegratedRuntimeConfig(**cfg_base, sleep_mode="integrated"))
    rt.body.sleep_pressure = 0.6
    rt.body.fatigue = 0.5
    integrated = rt.run()
    assert legacy["memory_replays"] == 0
    assert integrated["development_maturation"] >= 0.0


def test_integrated_v9_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v9.yaml")
    result = rt.run(50)
    assert result["profile"] == "integrated_v9"
    assert result["sleep_mode"] == "integrated"
