"""Tests bench helpers + E7 thalamic ablation signal."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE, SCALE_50K_PROFILE, profile_neuron_count
from experiments.bench_tick_gpu import bench_profile


def test_bench_compact_ok():
    row = bench_profile("compact", ticks=2, warmup=0, skip_heavy=True)
    assert row["ok"] is True
    assert row["ms_per_tick"] is not None
    assert row["active_lif"] == profile_neuron_count(COMPACT_PROFILE)


def test_bench_50k_skips_without_forcing_on_cpu_path():
    """Sin GPU, 50k se omite (no OOM en CI)."""
    from brain.backend import get_backend

    if get_backend().gpu_available:
        # Con GPU puede correr; solo verificamos que no crashea
        row = bench_profile("50k", ticks=1, warmup=0, skip_heavy=False)
        assert row["active_lif"] >= 50_000
        return
    row = bench_profile("50k", ticks=1, warmup=0, skip_heavy=True)
    assert row["skipped"] is True
    assert row["active_lif"] >= 50_000
    assert "GPU" in row["skip_reason"] or "gpu" in row["skip_reason"].lower()


def test_e7_vision_ablation_drops_thalamic_gain():
    sd = Path(tempfile.mkdtemp(prefix="nexo_e7t_"))
    flags = replace(AblationFlags(), enable_multimodal_delays=True, disable_hippocampus=True)
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    brain.sensory_hub.clear_ablation()
    brain.sensory_hub.route(brain, brain._scan_vision())
    g_full = float(brain.thalamus.gains.get("world", 1.0))

    brain.sensory_hub.set_ablation("vision")
    brain.sensory_hub.route(brain, brain._scan_vision())
    g_ablate = float(brain.thalamus.gains.get("world", 1.0))
    assert g_ablate < g_full
