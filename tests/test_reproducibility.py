"""Pruebas de reproducibilidad — RNG integrado sin parches manuales."""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pytest

from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE
from nexo.experiment_conditions import get_condition
from nexo.random_streams import RandomStreams
from nexo.result_schema import trajectory_hash


def _trajectory(
    seed: int,
    state_dir: Path,
    condition: str = "baseline_legacy",
    steps: int = 6,
) -> list[dict]:
    """Run ``steps`` ticks of a fresh brain and return its decision trace.

    ``state_dir`` must be empty and unique per call: memories persist even with
    ``auto_save=False``, so sharing a directory makes the second brain of a
    same-seed comparison start from the first one's recollections.
    """
    cond = get_condition(condition)
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        headless=True,
        auto_save=False,
        seed=seed,
        condition_id=cond.condition_id,
        experiment_flags=cond.flags,
        state_dir=state_dir,
    )
    rows = []
    for _ in range(steps):
        out = brain.world_tick(steps=1)
        delib = out.get("deliberation") or {}
        rows.append({"choice_key": delib.get("choice_key"), "agency": delib.get("agency")})
    return rows


def test_same_seed_reproduces_full_trajectory(tmp_path_factory: pytest.TempPathFactory):
    first = _trajectory(999, tmp_path_factory.mktemp("repro_a"), steps=6)
    second = _trajectory(999, tmp_path_factory.mktemp("repro_b"), steps=6)
    assert trajectory_hash(first) == trajectory_hash(second)


def test_different_seed_changes_stochastic_trajectory(tmp_path_factory: pytest.TempPathFactory):
    first = _trajectory(1, tmp_path_factory.mktemp("seed_a"), steps=6)
    second = _trajectory(2, tmp_path_factory.mktemp("seed_b"), steps=6)
    assert trajectory_hash(first) != trajectory_hash(second)


def test_each_stream_reproduces_independently():
    a = RandomStreams.from_root_seed(5)
    b = RandomStreams.from_root_seed(5)
    assert np.array_equal(a.world.random(50), b.world.random(50))
    assert np.array_equal(a.decision.random(50), b.decision.random(50))


def test_streams_do_not_share_identical_sequences():
    s = RandomStreams.from_root_seed(7)
    assert not np.array_equal(s.world.random(100), s.decision.random(100))


def test_brain_integrates_random_streams_without_manual_patch():
    brain = InfantApeBrain(profile=COMPACT_PROFILE, headless=True, auto_save=False, seed=123)
    assert brain.world._rng is brain.random_streams.world


def test_seed_is_present_in_every_result():
    brain = InfantApeBrain(profile=COMPACT_PROFILE, headless=True, auto_save=False, seed=77)
    assert brain.seed == 77
    assert brain.random_streams.root_seed == 77


def test_rng_is_not_recreated_from_age_ticks():
    import brain.deliberation as dm

    src = inspect.getsource(dm.PrefrontalDeliberation.run)
    assert "default_rng(int(brain.lifecycle.age_ticks" not in src


def test_roadmap100_full_v1_activates_memory():
    assert get_condition("roadmap100_full_v1").flags.enable_memory_dynamics is True


def test_roadmap100_no_binding_from_full():
    full = get_condition("roadmap100_full_v1")
    nb = get_condition("roadmap100_no_binding_v1")
    assert nb.flags.enable_memory_dynamics == full.flags.enable_memory_dynamics
    assert nb.flags.bind_deliberation is False


def test_baseline_differs_from_roadmap100_v1():
    assert get_condition("baseline_legacy").config_hash() != get_condition("roadmap100_full_v1").config_hash()
