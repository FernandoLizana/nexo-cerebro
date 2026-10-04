"""Tests for autonomous sleep study mode."""

from __future__ import annotations

from dataclasses import replace

import pytest

from brain import InfantApeBrain
from brain.experiment_flags import AblationFlags
from brain.profile import COMPACT_PROFILE
from brain.sleep_study import SleepStudyEngine, SleepStudyLog


@pytest.fixture
def brain(tmp_path):
    flags = replace(AblationFlags(), enable_sleep_study=True, enable_sleep_web=False)
    b = InfantApeBrain(profile=COMPACT_PROFILE, state_dir=tmp_path, experiment_flags=flags)
    b.headless = True
    return b


def test_sleep_study_disabled_by_default():
    b = InfantApeBrain(profile=COMPACT_PROFILE)
    assert b.experiment_flags.enable_sleep_study is False
    engine = SleepStudyEngine()
    assert engine.run_sleep_session(b)["count"] == 0


def test_sleep_study_repaso_writes_history(brain):
    row = brain.sleep_study._run_one_action(brain, phase="rem", source="test")
    assert row is not None
    assert brain.sleep_study.log.total_actions >= 1
    assert brain.sleep_study.log.entries[0]["kind"] in (
        "repaso",
        "curriculum",
        "brain_facts",
        "anatomy",
        "clinical",
        "biopsych",
        "infant_brain",
        "library",
    )


def test_sleep_study_does_not_write_choice_key(brain):
    before = brain.deliberation.last.choice_key
    brain.sleep_study._run_one_action(brain, phase="rem", source="test")
    after = brain.deliberation.last.choice_key
    assert after == before


def test_sleep_study_log_persistence(tmp_path):
    log = SleepStudyLog()
    from brain.sleep_study import SleepStudyEntry

    log.append(
        SleepStudyEntry(kind="repaso", title="hipocampo", phase="rem", source="test")
    )
    log.save(tmp_path)
    loaded = SleepStudyLog.load(tmp_path)
    assert loaded.total_actions == 1
    assert loaded.entries[0]["title"] == "hipocampo"


def test_sleep_architecture_rem_hook(brain):
    brain.brainstem.sleep_pressure = 0.9
    out = brain.sleep(cycles=1, steps_per_cycle=50)
    assert out.get("slept") is True
    assert "sleep_study" in out
    assert "sleep_study_log" in out
