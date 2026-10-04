"""Tests diálogo cuidador — respuestas coherentes sin Ollama."""

from __future__ import annotations

from brain.caregiver_dialogue import (
    caregiver_reply_fallback,
    is_fragmentary_speech,
    reply_engages_caregiver,
)


def test_calor_gets_coherent_reply():
    r = caregiver_reply_fallback(
        user_message="calor",
        mood="uneasy",
        room="salón",
        feelings=[{"signal": "hambre", "intensity": 0.6}],
    )
    assert "calor" in r.lower()
    assert "…hambre…" not in r
    assert len(r) > 20


def test_acknowledges_user_words():
    r = caregiver_reply_fallback(
        user_message="¿estás bien?",
        intent="question",
        mood="calm",
        room="jardín",
    )
    assert "?" in r or "claro" in r.lower() or "no lo" in r.lower()


def test_fragmentary_detected():
    assert is_fragmentary_speech("…hambre… cerca… calor…")
    assert is_fragmentary_speech("...hambre... imaginación: fin del cic... cerca... calor...")
    assert not is_fragmentary_speech("Sí, también siento calor en el salón.")


def test_no_te_entiendo_reply():
    r = caregiver_reply_fallback(
        user_message="No te entiendo nexos",
        mood="uneasy",
        room="salón",
    )
    assert "entiendo" in r.lower() or "perdona" in r.lower() or "escucho" in r.lower()
    assert is_fragmentary_speech(r) is False


def test_internal_dump_not_engaging():
    bad = "...hambre... imaginación: fin del cic... cerca... calor..."
    assert is_fragmentary_speech(bad)
    assert not reply_engages_caregiver("No te entiendo nexos", bad)

