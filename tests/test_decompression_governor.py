"""Tests DecompressionGovernor — presupuesto por tick."""

from __future__ import annotations

from brain.decompression_governor import DecompressionGovernor


def test_governor_resets_each_tick():
    g = DecompressionGovernor(max_bytes_per_tick=1000, max_assemblies=3)
    g.record(400, kind="assembly", label="a")
    g.record(300, kind="assembly", label="b")
    assert g.assemblies_used == 2
    g.reset_tick()
    assert g.bytes_used == 0
    assert g.assemblies_used == 0


def test_governor_blocks_over_budget():
    g = DecompressionGovernor(max_bytes_per_tick=500, max_assemblies=5)
    assert g.record(400, kind="assembly")
    assert not g.record(200, kind="assembly")
    assert g.blocked == 1


def test_priority_boost_increases_assembly_limit():
    g = DecompressionGovernor(max_assemblies=4)
    g.set_priorities(conscious_salience=0.9, surprise=0.5)
    assert g.priority_boost > 0.4
    base = g.effective_assembly_limit(2)
    g.reset_tick()
    g.set_priorities(conscious_salience=0.0, surprise=0.0)
    low = g.effective_assembly_limit(2)
    assert base >= low


def test_chunk_limit_respected():
    g = DecompressionGovernor(max_bytes_per_tick=100_000, max_chunks=2)
    assert g.record(100, kind="chunk")
    assert g.record(100, kind="chunk")
    assert not g.record(100, kind="chunk")
    assert g.chunks_used == 2


def test_prefetch_budget_separate_from_main():
    g = DecompressionGovernor(max_bytes_per_tick=100, prefetch_budget_bytes=500)
    assert g.record(90, kind="assembly")
    assert not g.record(20, kind="assembly")
    assert g.record_prefetch(400)
    assert g.prefetch_bytes_used == 400


def test_to_dict_has_expected_keys():
    g = DecompressionGovernor()
    d = g.to_dict()
    assert "bytes_used" in d
    assert "max_assemblies" in d
    assert "priority_boost" in d
    assert "lifetime_bytes" in d
    assert "prefetch_bytes_used" in d
