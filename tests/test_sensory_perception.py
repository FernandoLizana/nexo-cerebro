"""Bloque C — percepción sensorial ampliada (items 21–32)."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from brain.audition import AuditoryPathway
from brain.experiment_flags import AblationFlags
from brain.nociception import NociceptiveTerminal
from brain.superior_colliculus import SuperiorColliculus
from brain.vestibular import VestibularPathway
from brain.vision import SaccadeController, enrich_depth_2_5d


def test_auditory_bands_from_echo():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    aud = AuditoryPathway()
    pat, meta = aud.listen(brain, echo="hola cuidador")
    assert pat.size == brain.n_sensory
    assert meta["loudness"] > 0.4
    assert "mid_hz" in meta["bands"]


def test_superior_colliculus_fuses_vision_audio():
    sc = SuperiorColliculus()
    vision = {
        "foveal": [
            {"angle_deg": 10, "distance": 40, "salience": 0.7, "label": "nevera"},
        ],
    }
    audio = {"loudness": 0.5, "caregiver": True}
    out = sc.fuse(vision=vision, audio_meta=audio)
    assert out["peak"]["salience"] > 0.0
    assert sc.encode(16).size == 16


def test_saccade_promotes_peripheral():
    ctrl = SaccadeController()
    vision = {
        "peripheral": [{"id": "tv", "label": "TV", "salience": 0.8, "angle_deg": 30, "distance": 60}],
        "foveal": [],
    }
    out = ctrl.apply(vision, tick=16)
    assert out.get("saccade") is not None
    assert out["foveal"][0]["id"] == "tv"


def test_depth_2_5d_map():
    vision = enrich_depth_2_5d(
        {
            "foveal": [{"id": "a", "distance": 50, "salience": 0.5}],
            "peripheral": [],
            "percepts": [],
        }
    )
    assert vision["depth_map"][0]["depth_m"] == pytest.approx(0.5, abs=0.01)


def test_referred_pain_from_viscera():
    noc = NociceptiveTerminal()
    from brain.body import BodyState

    body = BodyState()
    noc.c_fiber["viscera"] = 0.7
    noc.apply_referred_pain(body)
    assert body.pain_limbs > 0.0 or body.pain_ache > 0.0


def test_baroreceptors_track_heart_rate():
    from brain.body import BodyState

    body = BodyState()
    body.update_baroreceptors(140.0)
    assert body.cardiac_arousal > 0.0


def test_vestibular_vertigo_on_ragdoll():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.biomech.ragdoll_active = True
    brain.biomech.equilibrium = 0.3
    vest = VestibularPathway()
    _, meta = vest.integrate(brain)
    assert meta["vertigo"] > 0.2


def test_sensory_stack_integration():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_advanced_sensory=True,
        enable_superior_colliculus=True,
        enable_referred_pain=True,
        enable_cardiac_interoception=True,
    )
    brain.nociceptor.c_fiber["viscera"] = 0.6
    out = brain.sensory_stack.tick(brain, vision={"foveal": [], "peripheral": []})
    assert "audition" in out["meta"]
    assert brain.sensory_stack.colliculus.peak_salience >= 0.0
