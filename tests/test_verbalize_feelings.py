"""Humanización de sensaciones para habla."""

from __future__ import annotations

from brain.language_cortex import LanguageContext, LanguageCortex, _dyad_sounds_broken
from brain.verbalize import humanize_feeling, humanize_visible


def test_pain_phrase():
    assert humanize_feeling("dolor pecho") == "me duele el pecho"
    assert humanize_feeling("dolor cabeza") == "me duele la cabeza"


def test_basic_feelings():
    assert humanize_feeling("hambre") == "tengo hambre"
    assert humanize_feeling("confort") == "estoy a gusto"


def test_visible_article():
    assert humanize_visible("cama") == "la cama"


def test_dyad_fallback_natural():
    ctx = LanguageContext(
        feelings=[{"signal": "dolor pecho", "intensity": 0.6}],
        visible_world=["cama"],
        chemistry={"attraction": 0.8},
        room="casa",
    )
    line = LanguageCortex()._dyad_verbal_fallback(ctx, "nexo")
    assert "dolor pecho" not in line.lower()
    assert "pecho" in line.lower()
    assert "estoy dolor" not in line.lower()


def test_broken_dyad_detected():
    assert _dyad_sounds_broken("Yo estoy dolor pecho.")
    assert not _dyad_sounds_broken("Me duele el pecho, Nira.")
