"""Motor de lenguaje neuro-inspirado (sin Ollama)."""

from __future__ import annotations

import os

from brain.language_cortex import LanguageContext, LanguageCortex
from brain.neural_language import NeuralLanguageEngine, resolve_language_backend


def _ctx(**kwargs) -> LanguageContext:
    return LanguageContext(**kwargs)


def test_resolve_backend_defaults_neural():
    os.environ.pop("CEREBRO_LANGUAGE", None)
    os.environ["CEREBRO_OLLAMA"] = "0"
    assert resolve_language_backend() == "neural"


def test_resolve_backend_ollama_legacy():
    os.environ.pop("CEREBRO_LANGUAGE", None)
    os.environ["CEREBRO_OLLAMA"] = "1"
    assert resolve_language_backend() == "ollama"


def test_compose_world_from_drives():
    eng = NeuralLanguageEngine()
    text, src = eng.compose_world(
        _ctx(
            room="cocina",
            drives={"seek_water": 0.8},
            feelings=[{"signal": "sed", "intensity": 0.7}],
        )
    )
    assert src == "neural"
    assert "sed" in text.lower() or "agua" in text.lower()


def test_compose_chat_greeting():
    eng = NeuralLanguageEngine()
    text, src = eng.compose_chat(
        _ctx(user_message="hola nexo", intent="greeting", room="casa")
    )
    assert src == "neural"
    assert "hola" in text.lower()
    assert len(text) > 20


def test_comprehend_topics():
    eng = NeuralLanguageEngine()
    parsed = eng.comprehend("¿cómo funciona el cerebro?", _ctx())
    assert parsed["intent_hint"] == "question"
    assert "cerebro" in parsed["topics"]


def test_compose_chat_study_topic():
    eng = NeuralLanguageEngine()
    text, src = eng.compose_chat(
        _ctx(
            user_message="¿qué has aprendido del cerebro?",
            intent="question",
            room="escritorio",
            study_tracks={
                "clinical": {
                    "progress": 0.11,
                    "total": 9,
                    "last_title": "Compromiso de consciencia",
                    "current_title": "Compromiso de consciencia",
                    "focus_ticks": 20,
                    "sections": [{"title": "Compromiso de consciencia", "done": True}],
                },
            },
        )
    )
    assert src == "neural"
    assert "consciencia" in text.lower() or "neurolog" in text.lower()


def test_study_voice_does_not_force_action():
    """Verbalización refleja estudio; no contiene imperativos de motor."""
    eng = NeuralLanguageEngine()
    text, _ = eng.compose_world(
        _ctx(
            study_tracks={
                "biopsych": {
                    "progress": 0.3,
                    "total": 10,
                    "last_title": "Neurotransmisores",
                    "focus_ticks": 30,
                    "sections": [],
                },
            },
            feelings=[{"signal": "curiosidad", "intensity": 0.5}],
        )
    )
    assert "Neurotransmisores" in text or "biopsicolog" in text.lower()
    assert "choice_key" not in text.lower()


def test_language_cortex_neural_backend():
    os.environ["CEREBRO_LANGUAGE"] = "neural"
    os.environ["CEREBRO_OLLAMA"] = "0"
    cortex = LanguageCortex()
    assert cortex.backend == "neural"
    assert cortex.enabled is False
    text, src = cortex.express(
        _ctx(
            mode="world",
            room="escritorio",
            feelings=[{"signal": "curiosidad", "intensity": 0.5}],
            visible_world=["libro"],
        )
    )
    assert src == "neural"
    assert len(text) > 10
