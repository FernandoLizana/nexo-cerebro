"""Currículo infantil — Mi primer libro del cerebro."""

from __future__ import annotations

from pathlib import Path

from .study_track import TrackSection, TrackState, get_section, load_track, study_section

_PATH = Path(__file__).resolve().parent.parent / "data" / "curriculum" / "infant_brain" / "sections.json"
SECTIONS: tuple[TrackSection, ...] = load_track(_PATH, track_name="infant_brain")
SECTION_BY_KEY = {s.key: s for s in SECTIONS}


def default_state() -> TrackState:
    return TrackState(sections=SECTIONS, track_name="infant_brain")


def study_infant_section(brain, section: TrackSection, *, sleep: bool = False) -> dict:
    return study_section(
        brain,
        brain.infant_brain,
        section,
        source="infant_brain",
        steps=14 if sleep else 24,
        sleep=sleep,
    )


def get_infant_section(key: str | None = None) -> TrackSection | None:
    return get_section(SECTIONS, key)
