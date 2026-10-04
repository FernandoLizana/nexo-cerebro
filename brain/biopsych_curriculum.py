"""Currículo Biological Psychology — fases 1–5."""

from __future__ import annotations

from pathlib import Path

from .study_track import TrackSection, TrackState, get_section, load_track, study_section

_PATH = Path(__file__).resolve().parent.parent / "data" / "curriculum" / "biopsych_phases" / "sections.json"
SECTIONS: tuple[TrackSection, ...] = load_track(_PATH, track_name="biopsych")
SECTION_BY_KEY = {s.key: s for s in SECTIONS}

PHASE_ORDER = (
    ("fundamentos", 1, "Fundamentos"),
    ("memoria_avanzada", 2, "Memoria avanzada"),
    ("emocion_basica", 3, "Emoción básica"),
    ("desarrollo", 4, "Desarrollo cerebral"),
    ("psicofarmacologia", 5, "Psicofarmacología"),
)


def default_state() -> TrackState:
    return TrackState(sections=SECTIONS, track_name="biopsych")


def study_biopsych_section(brain, section: TrackSection, *, sleep: bool = False) -> dict:
    return study_section(
        brain,
        brain.biopsych,
        section,
        source="biopsych",
        steps=20 if sleep else 30,
        sleep=sleep,
    )


def get_biopsych_section(key: str | None = None) -> TrackSection | None:
    return get_section(SECTIONS, key)
