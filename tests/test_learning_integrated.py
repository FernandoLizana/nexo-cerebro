"""Tests Sprint 6 — neuromodulación, TD learning y plasticidad."""

from __future__ import annotations

from nexo.connectome.plastic_connectivity import PlasticityState
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config
from nexo.neuromodulation.state import NeuromodulatorState
from nexo.reinforcement.td_learning import TDRewardSystem


def test_neuromodulator_responds_to_reward():
    mods = NeuromodulatorState()
    before = mods.dopamine
    mods.update(reward=0.8, stress=0.1, novelty=0.2, attention=0.5, sleep_pressure=0.1)
    assert mods.dopamine != before
    assert 0.0 <= mods.dopamine <= 1.0


def test_td_learning_updates_values():
    td = TDRewardSystem()
    d1 = td.observe(
        prev_drive="hunger",
        prev_energy_bucket=2,
        action="eat",
        reward=0.5,
        next_drive="hunger",
        next_energy_bucket=3,
    )
    assert td.updates == 1
    assert "room|hunger|2::eat" in td.values or td.last_state == "room|hunger|2"
    biases = td.go_biases(top_drive="hunger", energy_bucket=2, action_keys=("eat", "rest"))
    assert isinstance(biases, dict)


def test_plasticity_state_updates_bounded():
    plastic = PlasticityState()
    w1 = plastic.update("prefrontal", "basal_ganglia", 0.1)
    w2 = plastic.update("prefrontal", "basal_ganglia", 0.5)
    assert plastic.min_weight <= w2 <= plastic.max_weight
    assert w2 >= w1


def test_integrated_learning_emits_events():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=40,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="integrated",
            learning_mode="integrated",
            profile="test_v6",
        )
    )
    result = rt.run()
    types = {e.event_type for e in rt.state_store.event_log}
    assert "neuromodulation.updated" in types
    assert "td.updated" in types
    assert result["learning_mode"] == "integrated"
    assert result["td_updates"] > 0


def test_learning_integrated_vs_legacy_metrics():
    legacy = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=50,
            perception_mode="predictive",
            memory_mode="integrated",
            executive_mode="integrated",
            learning_mode="legacy",
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
        )
    ).run()
    assert legacy["td_updates"] == 0
    assert integrated["td_updates"] > 0
    assert integrated["neuromodulation_events"] > 0


def test_learning_reproducible():
    cfg = dict(
        seed=91,
        ticks=35,
        perception_mode="predictive",
        memory_mode="integrated",
        executive_mode="integrated",
        learning_mode="integrated",
    )
    r1 = IntegratedRuntime(IntegratedRuntimeConfig(**cfg)).run()
    r2 = IntegratedRuntime(IntegratedRuntimeConfig(**cfg)).run()
    assert r1["trajectory_hash"] == r2["trajectory_hash"]
    assert r1["td_updates"] == r2["td_updates"]


def test_integrated_v6_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v6.yaml")
    result = rt.run(40)
    assert result["profile"] == "integrated_v6"
    assert result["learning_mode"] == "integrated"
