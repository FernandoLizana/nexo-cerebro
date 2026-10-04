"""Currículo integrado en la simulación de Nexo."""

from brain.curriculum import SECTIONS, CurriculumState, get_section, study_section
from brain.mind import InfantApeBrain


def test_sections_count():
    assert len(SECTIONS) == 46


def test_suggest_next_in_order():
    st = CurriculumState()
    first = st.suggest_next()
    assert first is not None
    assert first.n == 1
    st.mark_studied(first.key)
    second = st.suggest_next()
    assert second is not None
    assert second.n == 2


def test_study_section_marks_progress():
    brain = InfantApeBrain()
    sec = get_section(key="neuron")
    assert sec is not None
    result = study_section(brain, sec)
    assert brain.curriculum.last_key == "neuron"
    assert "neuron" in brain.curriculum.completed
    assert result.get("learning", {}).get("episodes", 0) >= 1


def test_anatomy_focus_boost():
    from brain.curriculum import anatomy_focus_boost

    boosted = anatomy_focus_boost("hippocampus", 0.3, ["hippocampus"])
    plain = anatomy_focus_boost("hippocampus", 0.3, [])
    assert boosted > plain
