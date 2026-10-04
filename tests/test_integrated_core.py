"""Tests núcleo integrado Sprint 1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from nexo.core.clock import SimulationClock
from nexo.core.events import CognitiveEvent
from nexo.core.scheduler import CognitiveScheduler
from nexo.core.state_store import StateStore
from nexo.connectome.graph import ConnectomeGraph
from nexo.connectome.routing import ConnectomeRouter
from nexo.demo.room_scenario import RoomWorld
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo.random_streams import RandomStreams


ROOT = Path(__file__).resolve().parent.parent
CONNECTOME = ROOT / "configs/connectome/connectome_v1.yaml"


def test_simulation_clock_no_wall_time():
    clk = SimulationClock(seconds_per_tick=0.1)
    clk.advance(10)
    assert clk.tick == 10
    assert abs(clk.simulation_seconds - 1.0) < 1e-9
    assert 0.0 <= clk.circadian_phase < 1.0


def test_state_store_reducer_energy():
    store = StateStore()
    ev = CognitiveEvent(
        event_type="homeostatic.energy_changed",
        source="test",
        tick=1,
        simulation_time=0.1,
        payload={"delta": -0.1},
    )
    store.dispatch(ev)
    assert store.state.homeostatic.energy == pytest.approx(0.9)


def test_connectome_validates():
    graph = ConnectomeGraph.from_yaml(CONNECTOME)
    errors = graph.validate()
    assert not errors, errors


def test_same_seed_same_trajectory_integrated():
    r1 = IntegratedRuntime(IntegratedRuntimeConfig(seed=42, ticks=40))
    out1 = r1.run()
    r2 = IntegratedRuntime(IntegratedRuntimeConfig(seed=42, ticks=40))
    out2 = r2.run()
    assert out1["trajectory_hash"] == out2["trajectory_hash"]


def test_different_seed_different_trajectory():
    r1 = IntegratedRuntime(IntegratedRuntimeConfig(seed=42, ticks=40))
    r2 = IntegratedRuntime(IntegratedRuntimeConfig(seed=99, ticks=40))
    assert r1.run()["trajectory_hash"] != r2.run()["trajectory_hash"]


def test_substreams_reproducible():
    a = RandomStreams.from_root_seed(7)
    b = RandomStreams.from_root_seed(7)
    seq_a = a.world.random(20)
    seq_b = b.world.random(20)
    assert (seq_a == seq_b).all()
    assert not (a.decision.random(20) == a.world.random(20)).all()


def test_scheduler_runs_processes():
    streams = RandomStreams.from_root_seed(1)
    graph = ConnectomeGraph.from_yaml(CONNECTOME)
    world = RoomWorld()
    sched = CognitiveScheduler(
        clock=SimulationClock(),
        state_store=StateStore(),
        router=ConnectomeRouter(graph=graph, rng=streams.neural),
        rng=streams.decision,
        config={"world_state": world},
    )
    from nexo.core.process import BasalGangliaSelectorProcess, SensoryRelayProcess

    sched.register(SensoryRelayProcess())
    sched.register(BasalGangliaSelectorProcess())
    events = sched.run(15)
    assert len(events) > 0
    assert sched.clock.tick == 15


def test_room_world_no_hardcoded_success():
    world = RoomWorld(energy=0.2, food_available=True)
    out = world.apply_action("eat")
    assert out["reward"] > 0
    out_bad = world.apply_action("explore")
    assert out_bad["reward"] < out["reward"]


def test_integrated_demo_produces_actions_and_memory():
    rt = IntegratedRuntime(IntegratedRuntimeConfig(seed=123, ticks=60))
    result = rt.run()
    assert len(result["actions_taken"]) >= 10
    assert result["event_count"] > 20


def test_energy_stays_non_negative():
    rt = IntegratedRuntime(IntegratedRuntimeConfig(seed=5, ticks=100))
    rt.run()
    assert rt.state_store.state.homeostatic.energy >= 0.0


def test_result_records_seed():
    rt = IntegratedRuntime(IntegratedRuntimeConfig(seed=88, ticks=10))
    result = rt.run()
    assert result["seed"] == 88
