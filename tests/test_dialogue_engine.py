"""Motor de diálogo natural."""

from __future__ import annotations

from brain.dialogue_engine import (
    dyad_passes_quality,
    dyad_reply_fallback,
    humanized_feelings_block,
    is_meta_assistant_speech,
)
from brain.language_cortex import LanguageContext


def test_humanized_feelings_block():
    block = humanized_feelings_block(
        [{"signal": "hambre"}, {"signal": "dolor pecho"}]
    )
    assert "hambre" in block
    assert "pecho" in block
    assert "dolor pecho" not in block


def test_dyad_nexo_natural():
    ctx = LanguageContext(
        feelings=[{"signal": "dolor pecho", "intensity": 0.6}],
        visible_world=["cama"],
        chemistry={"attraction": 0.8},
        room="salón",
    )
    line = dyad_reply_fallback(ctx, "nexo")
    assert "dolor pecho" not in line
    assert "pecho" in line.lower()
    assert len(line.split()) >= 6


def test_dyad_nira_responds_to_partner():
    ctx = LanguageContext(
        partner_line="Nira, ¿qué te parece la cama?",
        feelings=[{"signal": "confort", "intensity": 0.5}],
        room="dormitorio",
        mood="calm",
    )
    line = dyad_reply_fallback(ctx, "nira")
    assert len(line) > 20
    assert "…" not in line[:6] or line.count("…") < 2


def test_rejects_meta_assistant_refusal_like_user_report():
    bad = (
        "¡No puedo proporcionar una respuesta detallada sobre las actividades y "
        "pensamientos de la persona basándome en el texto proporcionado. Sin embargo, "
        "puedo ofrecerte algunas preguntas o ideas generales que podrían ser relevantes "
        "para entender mejor su estado de ánimo y hábitos. **Actividades actuales:** "
        "* Se encuentra sentado cerca del sofá"
    )
    assert is_meta_assistant_speech(bad)
    assert not dyad_passes_quality(bad)
    short_refusal = "No puedo cumplir con esa solicitud. ¿Hay algo más con lo que pueda ayudarte?"
    assert is_meta_assistant_speech(short_refusal)
    assert not dyad_passes_quality(short_refusal)
    good = "Nira, estoy cerca del sofá y me siento un poco cansado. ¿Tú cómo estás?"
    assert not is_meta_assistant_speech(good)
    assert dyad_passes_quality(good)
