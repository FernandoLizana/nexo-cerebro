"""Tests for study tracks and library sleep study."""

from __future__ import annotations

from dataclasses import replace

import pytest

from brain import InfantApeBrain
from brain.clinical_neurology import SECTIONS as CLIN, get_clinical_section, study_clinical_section
from brain.biopsych_curriculum import SECTIONS as BIO, get_biopsych_section
from brain.infant_brain_curriculum import SECTIONS as INF
from brain.experiment_flags import AblationFlags
from brain.profile import COMPACT_PROFILE
from brain.study_track import TrackState


@pytest.fixture
def brain(tmp_path):
    flags = replace(AblationFlags(), enable_sleep_study=True, enable_sleep_web=False)
    b = InfantApeBrain(profile=COMPACT_PROFILE, state_dir=tmp_path, experiment_flags=flags)
    b.headless = True
    return b


def test_clinical_sections_loaded():
    assert len(CLIN) == 9
    sec = get_clinical_section("consciencia")
    assert sec is not None
    assert "GCS" in sec.teaching or "Glasgow" in sec.teaching or sec.title


def test_biopsych_has_phases():
    assert len(BIO) >= 5
    phases = {s.phase for s in BIO if s.phase}
    assert "fundamentos" in phases
    assert "psicofarmacologia" in phases


def test_infant_sections_loaded():
    assert len(INF) >= 4


def test_clinical_study_marks_progress(brain):
    sec = brain.clinical_neurology.suggest_next()
    assert sec is not None
    before = brain.deliberation.last.choice_key
    study_clinical_section(brain, sec)
    assert sec.key in brain.clinical_neurology.completed
    assert brain.deliberation.last.choice_key == before


def test_sleep_study_library_kind(brain, tmp_path):
    from brain.library import ensure_library, import_file

    lib = ensure_library()
    import_file(b"Hello library test content for Nexo.", "test-lib.txt")
    row = brain.sleep_study._run_one_action(brain, phase="rem", source="test")
    assert row is not None
    assert row["kind"] in (
        "repaso",
        "curriculum",
        "brain_facts",
        "anatomy",
        "clinical",
        "biopsych",
        "infant_brain",
        "library",
    )


def test_track_state_roundtrip():
    from brain.clinical_neurology import default_state

    st = default_state()
    st.mark_studied(CLIN[0].key)
    data = {
        "completed": list(st.completed),
        "current_key": st.current_key,
        "last_key": st.last_key,
        "study_count": st.study_count,
        "focus_ticks": st.focus_ticks,
        "focus_tags": list(st.focus_tags),
    }
    loaded = TrackState.from_dict(data, sections=CLIN, track_name="clinical_neurology")
    assert CLIN[0].key in loaded.completed
