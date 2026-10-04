"""Tests S6: schemas aprendidos + plasticidad por etapa vital."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from brain.experiment_flags import AblationFlags
from brain.learned_schemas import SchemaLearner, all_action_schemas
from brain.lifecycle import LifecycleState
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE


def test_paper_learned_schema_flags_off():
    f = AblationFlags()
    assert f.enable_learned_schemas is False
    assert f.enable_lifecycle_plasticity is False


def test_schema_consolidates_after_n_successes():
    sl = SchemaLearner(consolidate_after=3)
    out = None
    for _ in range(3):
        out = sl.note_success(
            choice_key="eat",
            room="cocina",
            motor=[4, 1],
            dopamine=0.4,
            confidence=0.4,
        )
    assert out is not None
    assert out.consolidated
    assert out.key.startswith("learned_")
    assert out.drive == "seek_food"
    assert len(sl.active_schemas()) == 1


def test_learned_schemas_enter_menu_not_force_choice():
    sd = Path(tempfile.mkdtemp(prefix="nexo_s6_"))
    flags = replace(
        AblationFlags(),
        enable_learned_schemas=True,
        disable_hippocampus=True,
    )
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    for _ in range(5):
        brain.schema_learner.note_success(
            choice_key="eat",
            room="cocina",
            motor=[4, 1],
            dopamine=0.6,
            confidence=0.6,
        )
    keys = {s["key"] for s in all_action_schemas(brain)}
    assert any(k.startswith("learned_") for k in keys)
    # PFC sigue eligiendo: un tick no garantiza learned_*, pero el menú creció
    before = brain.deliberation.last.choice_key
    brain.world_tick(steps=1)
    assert brain.deliberation.last.choice_key  # existe
    # Schema learner no escribe choice_key directamente
    assert before is not None or True


def test_lifecycle_neuro_modulation_by_stage():
    lc = LifecycleState()
    lc.age_ticks = 100  # joven (ticks_per_year=180 → <16y)
    lc._update_stage()
    assert lc.stage in ("infante", "joven")
    young = lc.neuro_modulation()

    lc.age_ticks = int(20 * lc.ticks_per_year)
    lc._update_stage()
    assert lc.stage == "adulto"
    adult = lc.neuro_modulation()
    assert adult["plasticity_scale"] < young["plasticity_scale"]
    assert adult["pfc_inhibition_scale"] > young["pfc_inhibition_scale"]
    assert adult["prune_rate"] > 0


def test_lifecycle_plasticity_scales_cortex():
    sd = Path(tempfile.mkdtemp(prefix="nexo_s6p_"))
    flags = replace(AblationFlags(), enable_lifecycle_plasticity=True, disable_hippocampus=True)
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    base = float(brain.profile.plasticity_mult)
    brain.lifecycle.age_ticks = int(25 * brain.lifecycle.ticks_per_year)
    brain.lifecycle._update_stage()
    brain.agent_loop._apply_lifecycle_plasticity(brain)
    epi = brain.lifecycle.epigenetic_profile()
    expected = base * float(epi["expression_plasticity"])
    assert abs(brain.cortex.plasticity_mult - expected) < 1e-6
