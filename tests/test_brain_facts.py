"""Tests Brain Facts 2018 integration."""

from brain.brain_facts import CHAPTERS, BrainFactsCorpus, get_chapter, study_chapter
from brain.circuit_hub import CIRCUIT_EDGES, CircuitHub
from brain.mind import InfantApeBrain


def test_manifest_has_chapters():
    assert len(CHAPTERS) >= 18
    ch = get_chapter("brain_basics")
    assert ch is not None
    assert "neuron" in ch.teaching.lower() or "brain" in ch.teaching.lower()
    assert ch.modules


def test_circuit_edges_cover_core_paths():
    labels = {e[3] for e in CIRCUIT_EDGES}
    assert "relevo sensorial" in labels
    assert "selección Go/No-Go" in labels
    assert "interocepción relevante" in labels


def test_study_chapter_updates_progress():
    brain = InfantApeBrain(headless=True)
    ch = get_chapter("senses")
    assert ch is not None
    result = study_chapter(brain, ch)
    assert ch.key in brain.brain_facts.completed
    assert brain.brain_facts.last_key == ch.key
    assert result.get("circuits")


def test_circuit_hub_tick():
    brain = InfantApeBrain(headless=True)
    out = brain.circuit_hub.tick(brain, vision={}, ambient={"hour": 14}, surprise=0.2)
    assert "signals" in out
    assert "brain_state" in out
    assert brain.cingulate.conflict_level >= 0
