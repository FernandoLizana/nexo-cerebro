"""Tests DecompressionPrefetcher — planificación predictiva."""

from __future__ import annotations

from dataclasses import replace

from brain.decompression_governor import DecompressionGovernor
from brain.decompression_prefetch import DecompressionPrefetcher
from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain


def test_prefetcher_predicts_deliberation_alternatives():
    brain = InfantApeBrain(headless=True)
    brain.experiment_flags = replace(
        brain.experiment_flags, enable_connectome_scaffold=True
    )
    pf = DecompressionPrefetcher()
    brain.cognition.run(
        brain,
        vision={"objects": []},
        drives=brain._merged_drives(),
        ambient=brain.world.ambient(),
    )
    plan = pf.predict_choice_keys(brain)
    assert plan
    assert plan[0][0] == brain.deliberation.last.choice_key


def test_prefetch_tick_respects_governor_budget():
    brain = InfantApeBrain(headless=True)
    brain.experiment_flags = replace(
        brain.experiment_flags, enable_connectome_scaffold=True
    )
    brain.decompress_governor = DecompressionGovernor(prefetch_budget_bytes=1)
    pf = DecompressionPrefetcher()
    brain.cognition.run(
        brain,
        vision={"objects": []},
        drives=brain._merged_drives(),
        ambient=brain.world.ambient(),
    )
    stats = pf.run_tick(brain)
    assert "plan" in stats
    assert stats["total_warmed"] >= 0


def test_governor_cumulative_persist_roundtrip():
    g = DecompressionGovernor()
    g.bytes_used = 1000
    g.prefetch_bytes_used = 200
    g.finalize_tick()
    saved = g.cumulative_dict()
    g2 = DecompressionGovernor()
    g2.load_cumulative(saved)
    assert g2.lifetime_bytes == 1000
    assert g2.lifetime_prefetch_bytes == 200
    assert g2.lifetime_ticks == 1
