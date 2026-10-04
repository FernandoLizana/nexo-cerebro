"""Tests configuraciones experimentales v1."""

from __future__ import annotations

from nexo.experiment_conditions import (
    find_unclassified_enable_flags,
    get_condition,
    roadmap100_full_v1_flags,
    roadmap100_no_binding_v1_flags,
)


def test_baseline_legacy_roadmap_off():
    f = get_condition("baseline_legacy").flags
    assert f.enable_memory_dynamics is False


def test_unclassified_enable_flags_empty():
    assert find_unclassified_enable_flags() == set()


def test_roadmap100_no_binding_from_full_not_baseline():
    full = roadmap100_full_v1_flags()
    nb = roadmap100_no_binding_v1_flags()
    assert nb.enable_memory_dynamics == full.enable_memory_dynamics
    assert nb.bind_deliberation is False
    assert get_condition("legacy_no_binding").flags.enable_memory_dynamics is False


def test_config_hash_stable():
    h1 = get_condition("roadmap100_full_v1").config_hash()
    h2 = get_condition("roadmap100_full_v1").config_hash()
    assert h1 == h2 and len(h1) == 64


def test_condition_families_distinct():
    assert get_condition("baseline_legacy").condition_family != get_condition("roadmap100_full_v1").condition_family
