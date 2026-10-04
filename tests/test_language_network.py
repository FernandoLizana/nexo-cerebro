"""Red de lenguaje — intercambio cuidador."""

from __future__ import annotations

from brain.caregiver_dialogue import caregiver_reply_fallback, is_fragmentary_speech
from brain.mind import InfantApeBrain


def test_needs_question_natural():
    r = caregiver_reply_fallback(
        user_message="diganme que necesitan",
        feelings=[
            {"signal": "dolor pecho", "intensity": 0.6},
            {"signal": "hambre", "intensity": 0.4},
        ],
        room="casa",
    )
    assert is_fragmentary_speech(r) is False
    assert "necesit" in r.lower() or "escucho" in r.lower()
    assert "dolor pecho" not in r
    assert "pecho" in r.lower() or "hambre" in r.lower()


def test_caregiver_network_no_fragment_dump():
    brain = InfantApeBrain()
    brain.language.enabled = False
    out = brain.caregiver_speak("diganme que necesitan")
    reply = out.get("reply") or ""
    assert is_fragmentary_speech(reply) is False
    assert out.get("language", {}).get("network")
