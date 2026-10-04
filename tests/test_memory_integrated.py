"""Tests Sprint 4 — memoria de trabajo e hipocampo integrado."""

from __future__ import annotations

import numpy as np

from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config
from nexo.memory.hippocampus.episode import EpisodicMemory
from nexo.memory.hippocampus.store import HippocampalStore
from nexo.random_streams import RandomStreams
from nexo.working_memory.buffer import WorkingMemoryBuffer


def _episode(emb: tuple[float, ...], *, action: str = "eat") -> EpisodicMemory:
    return EpisodicMemory(
        episode_id="ep1",
        event_embedding=emb,
        spatial_context=(0.5, 0.1),
        temporal_context=(1.0, 0.0),
        body_context=(0.8, 0.1, 0.0),
        affective_context=(0.2, 0.3, 0.0),
        action=action,
        outcome="reward=0.2",
        confidence=0.7,
        source_identity="self",
        tick=1,
        modality="food",
    )


def test_pattern_separation_diverges_similar_embeddings():
    store = HippocampalStore(separation_threshold=0.92)
    rng = RandomStreams.from_root_seed(1).memory
    base = (0.9, 0.1, 0.05)
    store.encode(_episode(base), rng=rng)
    separated = store.encode(_episode(base), rng=rng)
    assert separated is not None
    assert separated.event_embedding != base


def test_pattern_completion_is_imperfect():
    store = HippocampalStore(completion_noise=0.08)
    rng_a = RandomStreams.from_root_seed(2).memory
    rng_b = RandomStreams.from_root_seed(2).memory
    emb = (0.7, 0.2, 0.1)
    store.encode(_episode(emb), rng=rng_a)
    retrieved, sim = store.retrieve_partial(emb, rng=rng_b, top_k=1)[0]
    assert sim > 0.5
    assert retrieved.event_embedding != emb


def test_working_memory_respects_capacity():
    buf = WorkingMemoryBuffer(capacity=3)
    for i in range(6):
        buf.gate_in(f"m{i}", embedding=(float(i), 0.1, 0.0), tick=i, priority=0.5 + i * 0.1)
    assert len(buf.items) <= 3


def test_integrated_memory_mode_emits_events():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=40,
            perception_mode="predictive",
            memory_mode="integrated",
            profile="test_v4",
        )
    )
    result = rt.run()
    assert result["memory_mode"] == "integrated"
    types = {e.event_type for e in rt.state_store.event_log}
    assert "memory.encoded" in types or result["hippocampal_episodes"] >= 0
    assert "working_memory.updated" in types


def test_integrated_memory_reproducible():
    cfg = dict(
        seed=77,
        ticks=35,
        perception_mode="predictive",
        memory_mode="integrated",
    )
    r1 = IntegratedRuntime(IntegratedRuntimeConfig(**cfg)).run()
    r2 = IntegratedRuntime(IntegratedRuntimeConfig(**cfg)).run()
    assert r1["trajectory_hash"] == r2["trajectory_hash"]
    assert r1["memory_encodings"] == r2["memory_encodings"]


def test_integrated_memory_changes_metrics_vs_legacy():
    v3 = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=50, perception_mode="predictive", memory_mode="legacy")
    ).run()
    v4 = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=50, perception_mode="predictive", memory_mode="integrated")
    ).run()
    assert v3["memory_mode"] == "legacy"
    assert v4["memory_mode"] == "integrated"
    assert v3["memory_retrievals"] == 0
    assert v4["memory_retrievals"] > 0


def test_integrated_v4_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v4.yaml")
    result = rt.run(40)
    assert result["profile"] == "integrated_v4"
    assert result["memory_mode"] == "integrated"
    assert result["perception_mode"] == "predictive"
