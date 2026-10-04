"""Bloque H — lenguaje y comunicación (items 77–84)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from brain.experiment_flags import AblationFlags
from brain.language_cortex import LanguageContext
from brain.language_dynamics import LanguageDynamicsStack, study_tracks_snapshot
from brain.language_network import ComprehensionPacket
from brain.neural_language import NeuralLanguageEngine, resolve_language_backend


def test_neural_backend_default():
    import os

    os.environ["CEREBRO_LANGUAGE"] = "neural"
    os.environ["CEREBRO_OLLAMA"] = "0"
    assert resolve_language_backend() == "neural"


def test_prosody_high_arousal():
    stack = LanguageDynamicsStack()
    text, meta = stack.apply_prosody("Estoy bien", valence=0.2, arousal=0.85)
    assert text.endswith("!")
    assert meta["pace"] == "fast"


def test_inner_vs_outer_speech():
    stack = LanguageDynamicsStack()
    inner = stack.apply_inner_speech("pienso en comida")
    outer = stack.apply_outer_speech("…pienso en comida…")
    assert inner.startswith("…")
    assert inner.endswith("…")
    assert not outer.startswith("…")


def test_broca_aphasia_telegraphic():
    stack = LanguageDynamicsStack()
    stack.aphasia.broca = 0.6
    out = stack.apply_broca_aphasia("Quiero ir a la cocina porque tengo hambre")
    assert len(out.split()) < 7
    assert out.endswith("…")


def test_wernicke_distortion():
    stack = LanguageDynamicsStack()
    stack.aphasia.wernicke = 0.5
    packet = ComprehensionPacket(
        raw_text="hola",
        intent="greeting",
        topics=["casa"],
        source="neural_wernicke",
    )
    out = stack.distort_wernicke(packet)
    assert out.intent != "greeting" or out.topics != ["casa"]


def test_bilingual_code_switch():
    stack = LanguageDynamicsStack()
    out = stack.code_switch_reply("Hola, gracias por venir.", user_message="Hello, how are you?")
    assert "hi" in out.lower() or "thanks" in out.lower()


def test_seven_track_snapshot():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    snap = study_tracks_snapshot(brain)
    assert "curriculum" in snap
    assert "brain_facts" in snap
    assert "anatomy" in snap
    assert "clinical" in snap
    assert "library" in snap


def test_curriculum_verbalization():
    eng = NeuralLanguageEngine()
    text, src = eng.compose_chat(
        LanguageContext(
            user_message="¿qué has aprendido del cerebro?",
            intent="question",
            room="escritorio",
            study_tracks={
                "brain_facts": {
                    "progress": 0.2,
                    "total": 10,
                    "last_title": "Neuronas y sinapsis",
                    "current_title": "Neuronas y sinapsis",
                    "focus_ticks": 20,
                    "sections": [{"title": "Neuronas y sinapsis", "done": True}],
                },
            },
        )
    )
    assert src == "neural"
    low = text.lower()
    assert "neuron" in low or "brain facts" in low or "estudi" in low


def test_tutor_rag_enabled():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_language_dynamics=True,
        enable_language_tutor_rag=True,
    )
    stack = LanguageDynamicsStack()
    assert stack.ensure_tutor(brain)
    assert brain.language_network.tutor.enabled


def test_post_articulate_channels():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_language_dynamics=True,
        enable_inner_outer_speech=True,
        enable_prosody=False,
    )
    ctx = LanguageContext(user_message="", valence=0.1, arousal=0.3)
    inner = brain.language_dynamics.post_articulate(brain, "pienso en agua", ctx, channel="inner")
    outer = brain.language_dynamics.post_articulate(brain, "Tengo sed", ctx, channel="outer")
    assert inner.startswith("…")
    assert outer.endswith(".")
