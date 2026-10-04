"""Tests Sprint S3: WM limitada + atención competitiva (sin usurpar agency)."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from brain.attention import competitive_filter
from brain.experiment_flags import AblationFlags, apply_condition
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE
from brain.working_memory import WorkingMemory


def _brain(**kwargs) -> InfantApeBrain:
    sd = Path(tempfile.mkdtemp(prefix="nexo_s3_"))
    return InfantApeBrain(
        profile=COMPACT_PROFILE,
        headless=True,
        auto_save=False,
        state_dir=sd,
        **kwargs,
    )


def test_wm_capacity_evicts_and_raises_load():
    wm = WorkingMemory(capacity=3, limited=True)
    for i in range(5):
        wm.push(label=f"item-{i}", salience=0.2 + 0.1 * i)
    assert len(wm.slots) == 3
    assert wm.drops >= 2
    assert wm.load == 1.0
    assert wm.interference > 0
    assert wm.pfc_gain_scale() < 1.0


def test_wm_unlimited_when_flag_off():
    wm = WorkingMemory(capacity=7, limited=False)
    for i in range(20):
        wm.push(label=f"x-{i}", salience=0.5)
    assert len(wm.slots) <= 64
    assert wm.pfc_gain_scale() == 1.0


def test_attention_pain_wins_bottom_up():
    percepts = [
        {"label": "escritorio", "salience": 0.4, "kind": "desk"},
        {"label": "dolor corporal", "salience": 0.5, "kind": "pain"},
        {"label": "TV", "salience": 0.35, "kind": "tv"},
    ]
    attended, ignored, st = competitive_filter(
        percepts,
        drives={"seek_curiosity": 0.8},
        acetylcholine=0.4,
        goal="estudiar",
        budget=2,
    )
    assert attended
    assert attended[0]["kind"] == "pain"
    assert st.focus_source in ("bottom_up", "mixed")
    assert "agency_note" in st.to_dict()


def test_attention_top_down_boosts_goal():
    percepts = [
        {"label": "TV lejos", "salience": 0.55, "kind": "tv"},
        {"label": "escritorio listo", "salience": 0.4, "kind": "desk"},
    ]
    attended, _, st = competitive_filter(
        percepts,
        drives={"seek_curiosity": 0.9},
        acetylcholine=0.85,
        goal="estudiar neurociencia (navigate)",
        budget=2,
    )
    labels = " ".join(a["label"] for a in attended).lower()
    assert "escritorio" in labels or st.top_down_weight > 0


def test_paper_defaults_wm_attention_off():
    f = AblationFlags()
    assert f.enable_limited_wm is False
    assert f.enable_attention_budget is False
    assert apply_condition("full").enable_limited_wm is False


def test_demo_flags_enable_s3():
    flags = replace(
        AblationFlags(),
        enable_limited_wm=True,
        enable_attention_budget=True,
        disable_hippocampus=True,
    )
    brain = _brain(experiment_flags=flags)
    assert brain.working_memory.limited is True
    out = brain.world_tick(steps=1)
    cog = out.get("cognition") or {}
    att = (cog.get("attention") or {}).get("budget") or {}
    assert "focus_source" in att or att.get("budget") is not None
    snap = brain.snapshot()
    assert "working_memory" in snap
    assert snap["working_memory"]["limited"] is True
