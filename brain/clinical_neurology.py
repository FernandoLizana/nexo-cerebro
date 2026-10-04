"""Currículo clínico — Manual de Neurología UDD (9 capítulos)."""

from __future__ import annotations

from pathlib import Path

from .study_track import TrackSection, TrackState, get_section, load_track, study_section

_PATH = Path(__file__).resolve().parent.parent / "data" / "curriculum" / "clinical_neurology_uddl" / "sections.json"
SECTIONS: tuple[TrackSection, ...] = load_track(_PATH, track_name="clinical_neurology")
SECTION_BY_KEY = {s.key: s for s in SECTIONS}


def default_state() -> TrackState:
    return TrackState(sections=SECTIONS, track_name="clinical_neurology")


def study_clinical_section(brain, section: TrackSection, *, sleep: bool = False) -> dict:
    return study_section(
        brain,
        brain.clinical_neurology,
        section,
        source="clinical_neurology",
        steps=22 if sleep else 32,
        sleep=sleep,
    )


def get_clinical_section(key: str | None = None) -> TrackSection | None:
    return get_section(SECTIONS, key)
