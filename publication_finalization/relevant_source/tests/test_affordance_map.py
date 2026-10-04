"""Nexo Level 2.1: aprendizaje causal sin usurpar deliberación PFC."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from brain.affordance_map import AFFORDANCE_BIAS_MAX, AffordanceMap
from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE


def _transition(thirst_before: float, thirst_after: float) -> tuple[dict, dict]:
    before = {
        "hunger": 0.2,
        "thirst": thirst_before,
        "fatigue": 0.2,
        "comfort": 0.4,
        "bladder": 0.1,
        "hygiene": 0.1,
        "pain": 0.0,
        "pleasure": 0.0,
    }
    after = {**before, "thirst": thirst_after}
    return before, after


def _observe_water(
    affordances: AffordanceMap,
    *,
    object_id: str = "source-a",
    thirst_before: float = 0.8,
    thirst_after: float = 0.35,
):
    before, after = _transition(thirst_before, thirst_after)
    return affordances.observe(
        event={
            "type": "drink",
            "object_type": "water_source",
            "object_id": object_id,
            "target": object_id,
        },
        before=before,
        after=after,
        dominant_drive="seek_water",
        room="arena",
        decision_key="drink",
    )


def test_affordance_learns_observed_consequence_and_confidence():
    affordances = AffordanceMap()
    first = _observe_water(affordances)
    assert first is not None
    first_confidence = first.confidence
    assert first.mean_homeostasis_gain > 0.4
    assert first.success_count == 1

    for _ in range(4):
        _observe_water(affordances)
    assert first.observation_count == 5
    assert first.confidence > first_confidence
    assert first.expected_outcomes["thirst"] < -0.4


def test_failed_prediction_reduces_confidence():
    affordances = AffordanceMap()
    record = _observe_water(affordances)
    assert record is not None
    confidence_before = record.confidence
    _observe_water(affordances, thirst_before=0.8, thirst_after=0.8)
    assert record.failure_count == 1
    assert record.confidence < confidence_before
    assert record.mean_prediction_error > 0


def test_object_instances_remain_distinct():
    affordances = AffordanceMap()
    _observe_water(affordances, object_id="blue-fountain")
    _observe_water(affordances, object_id="red-fountain")
    assert len(affordances.records) == 2
    assert {r.object_id for r in affordances.records.values()} == {
        "blue-fountain",
        "red-fountain",
    }


def test_affordance_evidence_is_bounded_and_does_not_choose():
    affordances = AffordanceMap()
    for _ in range(20):
        _observe_water(affordances)
    choice_holder = {"choice_key": "wander"}
    biases = affordances.biases_for(
        candidate_keys=["drink", "wander"],
        dominant_drive="seek_water",
        room="arena",
    )
    assert 0 < biases["drink"] <= AFFORDANCE_BIAS_MAX
    assert choice_holder["choice_key"] == "wander"
    assert affordances.last_evidence[0].source_object == "source-a"


def test_affordance_persistence_round_trip(tmp_path: Path):
    first = AffordanceMap()
    first.bind_state_dir(tmp_path)
    _observe_water(first, object_id="novel-well")
    assert first.save()

    restored = AffordanceMap()
    restored.bind_state_dir(tmp_path)
    assert len(restored.records) == 1
    record = next(iter(restored.records.values()))
    assert record.object_id == "novel-well"
    assert record.observation_count == 1
    assert restored.load_error == ""


def test_corrupt_persistence_fails_closed(tmp_path: Path):
    (tmp_path / "affordances.json").write_text("{bad json", encoding="utf-8")
    affordances = AffordanceMap()
    affordances.bind_state_dir(tmp_path)
    assert affordances.records == {}
    assert "JSONDecodeError" in affordances.load_error


def test_real_drink_event_observes_before_after_without_forcing_choice():
    state_dir = Path(tempfile.mkdtemp(prefix="nexo_aff_"))
    flags = replace(
        AblationFlags(),
        enable_affordance_learning=True,
        disable_hippocampus=True,
    )
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=state_dir,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    brain.body.thirst = 0.85
    choice_before = brain.deliberation.last.choice_key
    brain.agent_loop._handle_world_event_with_affordance(
        brain,
        event={
            "type": "drink",
            "target": "fuente desconocida",
            "object_id": "novel-source",
            "object_type": "water_source",
        },
        last_ep=None,
        drives={"seek_water": 0.9},
        decision_key=choice_before,
    )
    assert brain.body.thirst < 0.5
    assert len(brain.affordance_map.records) == 1
    record = next(iter(brain.affordance_map.records.values()))
    assert record.candidate_key == "drink"
    assert record.object_type == "water_source"
    assert brain.deliberation.last.choice_key == choice_before


def test_pfc_consumes_affordance_evidence_but_selects_the_winner():
    state_dir = Path(tempfile.mkdtemp(prefix="nexo_aff_pfc_"))
    flags = replace(
        AblationFlags(),
        enable_affordance_learning=True,
        disable_hippocampus=True,
    )
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=state_dir,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    for _ in range(12):
        _observe_water(brain.affordance_map)
    result = brain.deliberation.run(
        brain,
        drives={"seek_water": 0.9},
        ambient={"hour": 12},
        attended=[],
        habit=None,
        surprise=0.0,
    )
    selected = [contestant for contestant in result.contestants if contestant.selected]
    assert len(selected) == 1
    assert result.choice_key == selected[0].key
    assert brain.affordance_map.last_evidence
    assert abs(brain.affordance_map.last_evidence[0].bias) <= AFFORDANCE_BIAS_MAX


def test_paper_default_affordances_off():
    assert AblationFlags().enable_affordance_learning is False
