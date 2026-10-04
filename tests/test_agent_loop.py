"""Tests Neural Agent Loop, GoalStack y Connectome Scaffold."""

from __future__ import annotations

from dataclasses import replace as dc_replace
from pathlib import Path

import numpy as np

from brain.connectome_blueprint import ConnectomeBlueprint
from brain.cortical_chunks import CorticalChunkStore
from brain.experiment_flags import AblationFlags
from brain.goal_stack import GoalStack
from brain.mind import InfantApeBrain


def test_connectome_blueprint_seed_stable():
    a = ConnectomeBlueprint(seed=42)
    b = ConnectomeBlueprint(seed=42)
    assert a.logical_neurons == b.logical_neurons
    assert a.estimate_logical_synapses() == b.estimate_logical_synapses()
    assert a.region_for_choice("eat") == "lobe_frontal"


def test_cortical_chunk_same_seed_same_pattern(tmp_path: Path):
    bp = ConnectomeBlueprint(seed=7)
    store = CorticalChunkStore(blueprint=bp, cache_dir=tmp_path / "test_chunks")
    c1 = store.load_chunk("lobe_frontal", 1, 2, 3, dim=128)
    c2 = store.load_chunk("lobe_frontal", 1, 2, 3, dim=128)
    assert np.allclose(c1.pattern, c2.pattern)


def test_goal_stack_navigate_then_interact():
    gs = GoalStack()
    assert gs.push_from_deliberation("eat", "comer")
    assert gs.depth() == 2
    assert gs.peek().phase == "navigate"
    assert gs.on_interact_complete("fridge")
    assert gs.depth() == 0


def test_deliberation_rechoice_penalty():
    brain = InfantApeBrain()
    delib = brain.deliberation
    delib.set_penalty("wander", 0.5)
    delib.run(
        brain,
        drives={"seek_food": 0.1, "sleep_need": 0.05},
        ambient={"hour": 12},
        attended=[],
        habit=None,
        surprise=0.1,
    )
    wander = next(c for c in delib.last.contestants if c.key == "wander")
    delib.clear_penalties()
    delib.run(
        brain,
        drives={"seek_food": 0.1, "sleep_need": 0.05},
        ambient={"hour": 12},
        attended=[],
        habit=None,
        surprise=0.1,
    )
    wander2 = next(c for c in delib.last.contestants if c.key == "wander")
    assert wander.net <= wander2.net


def test_world_tick_headless_agent_loop():
    brain = InfantApeBrain()
    brain.headless = True
    out = brain.world_tick(steps=1)
    assert "deliberation" in out
    assert "agent_loop" in out
    assert "connectome" in out
    assert out["connectome"]["logical_neurons"] >= 86_000_000_000


def test_scaffold_connectome_metrics_always_present():
    brain = InfantApeBrain()
    brain.headless = True
    snap = brain.snapshot()
    assert snap["connectome_scaffold"]["logical_neurons"] >= 86_000_000_000
    assert snap["connectome_scaffold"]["active_neurons"] > 0
