"""Fase 2 — tutor en sombra + RAG."""

from __future__ import annotations

from brain.language_network import LanguageNetwork
from brain.language_tutor_rag import (
    adapt_learned_exemplar,
    parse_tutor_label,
    tutor_memory_label,
)
from brain.language_cortex import LanguageContext
from brain.mind import InfantApeBrain


def test_tutor_label_roundtrip():
    label = tutor_memory_label(
        user_message="diganme que necesitan",
        exemplar="Te escucho. Tengo hambre y me duele el pecho.",
    )
    user, ex = parse_tutor_label(label)
    assert "necesitan" in user
    assert "hambre" in ex


def test_adapt_learned_exemplar():
    ctx = LanguageContext(
        user_message="hola",
        feelings=[{"signal": "hambre", "intensity": 0.7}],
        room="cocina",
    )
    out = adapt_learned_exemplar(
        "Hola, te escucho bien. Estoy aquí contigo.",
        "hola",
        ctx,
    )
    assert out
    assert "hambre" in out.lower() or "tengo hambre" in out.lower()


def test_learn_and_recall_via_rag():
    brain = InfantApeBrain()
    brain.language.enabled = False
    net = brain.language_network
    net.tutor.enabled = False
    net.learn_from_tutor(
        brain,
        user_message="qué necesitas",
        exemplar="Necesito agua y descanso, gracias por preguntar.",
        intent="question",
    )
    hits = brain.memory_store.search_language_tutor("qué necesitas", k=2, threshold=0.35)
    assert hits
    ctx = brain._language_context(user_message="qué necesitas", mode="chat")
    exchange = net.caregiver_exchange(brain, "qué necesitas", ctx, brain.language)
    assert exchange.reply
    assert "…" not in exchange.reply[:8] or exchange.source == "learned"
