"""
Currículos estructurados reutilizables — Manual UDD, Biopsych, infantil, etc.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass(frozen=True)
class TrackSection:
    n: int
    key: str
    title: str
    teaching: str
    track: str
    anatomy: tuple[str, ...] = ()
    transmitters: tuple[str, ...] = ()
    clinical_tools: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    phase: str = ""
    phase_n: int = 0
    valence: float = 0.12
    arousal: float = 0.38
    novelty: float = 0.55
    library_path: str = ""

    @property
    def all_tags(self) -> list[str]:
        base = list(self.tags) or [self.track, f"section:{self.n:02d}", f"topic:{self.key}"]
        if self.phase:
            base.append(f"phase:{self.phase}")
        return base

    def to_dict(self, *, done: bool = False) -> dict[str, Any]:
        return {
            "n": self.n,
            "key": self.key,
            "title": self.title,
            "track": self.track,
            "phase": self.phase or None,
            "phase_n": self.phase_n,
            "anatomy": list(self.anatomy),
            "transmitters": list(self.transmitters),
            "clinical_tools": list(self.clinical_tools),
            "done": done,
            "preview": self.teaching[:120] + ("…" if len(self.teaching) > 120 else ""),
            "library_path": self.library_path or None,
        }


def load_track(path: Path, *, track_name: str) -> tuple[TrackSection, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: list[TrackSection] = []
    for item in raw:
        out.append(
            TrackSection(
                n=int(item["n"]),
                key=str(item["key"]),
                title=str(item["title"]),
                teaching=str(item.get("teaching") or ""),
                track=track_name,
                anatomy=tuple(item.get("anatomy") or ()),
                transmitters=tuple(item.get("transmitters") or ()),
                clinical_tools=tuple(item.get("clinical_tools") or ()),
                tags=tuple(item.get("tags") or ()),
                phase=str(item.get("phase") or ""),
                phase_n=int(item.get("phase_n") or 0),
                valence=float(item.get("valence", 0.12)),
                arousal=float(item.get("arousal", 0.38)),
                novelty=float(item.get("novelty", 0.55)),
                library_path=str(item.get("library_path") or ""),
            )
        )
    return tuple(sorted(out, key=lambda s: s.n))


@dataclass
class TrackState:
    sections: tuple[TrackSection, ...]
    track_name: str
    completed: set[str] = field(default_factory=set)
    current_key: str | None = None
    last_key: str | None = None
    study_count: int = 0
    focus_ticks: int = 0
    focus_tags: list[str] = field(default_factory=list)

    def suggest_next(self) -> TrackSection | None:
        for sec in self.sections:
            if sec.key not in self.completed:
                return sec
        return self.sections[0] if self.sections else None

    def mark_studied(self, key: str) -> None:
        self.completed.add(key)
        self.last_key = key
        self.current_key = key
        self.study_count += 1
        for sec in self.sections:
            if sec.key == key:
                self.focus_tags = list(sec.all_tags[:6])
                self.focus_ticks = 48
                break

    def progress_ratio(self) -> float:
        if not self.sections:
            return 0.0
        return len(self.completed) / len(self.sections)

    def tick_focus(self) -> None:
        if self.focus_ticks > 0:
            self.focus_ticks -= 1
        if self.focus_ticks <= 0:
            self.focus_tags = []

    def to_dict(self) -> dict[str, Any]:
        current = next((s for s in self.sections if s.key == self.current_key), None)
        last = next((s for s in self.sections if s.key == self.last_key), None)
        phases = sorted({s.phase for s in self.sections if s.phase})
        return {
            "track": self.track_name,
            "total": len(self.sections),
            "completed": len(self.completed),
            "progress": round(self.progress_ratio(), 3),
            "current_key": self.current_key,
            "current_title": current.title if current else None,
            "last_key": self.last_key,
            "last_title": last.title if last else None,
            "study_count": self.study_count,
            "focus_ticks": self.focus_ticks,
            "focus_tags": list(self.focus_tags),
            "phases": phases,
            "sections": [s.to_dict(done=s.key in self.completed) for s in self.sections],
        }

    @classmethod
    def from_dict(cls, data: dict | None, sections: tuple[TrackSection, ...], track_name: str) -> TrackState:
        if not data:
            return cls(sections=sections, track_name=track_name)
        completed = data.get("completed")
        if completed is None and data.get("sections"):
            completed = [s["key"] for s in data["sections"] if s.get("done")]
        return cls(
            sections=sections,
            track_name=track_name,
            completed=set(completed or []),
            current_key=data.get("current_key"),
            last_key=data.get("last_key"),
            study_count=int(data.get("study_count") or 0),
            focus_ticks=int(data.get("focus_ticks") or 0),
            focus_tags=list(data.get("focus_tags") or data.get("focus_anatomy") or []),
        )


def apply_track_effects(brain: InfantApeBrain, section: TrackSection) -> None:
    brain.affect.process_stimulus(
        valence=section.valence,
        arousal=section.arousal,
        novelty=section.novelty,
        pain=0.0,
        social_bond=0.06,
        attention=0.58,
        surprise=0.14,
    )
    brain.affect.step()
    brain.affect.sync_modulators(brain.modulators)
    brain.affect.sync_hypothalamus(
        brain.hypothalamus,
        valence=section.valence,
        arousal=section.arousal,
    )
    for tid in section.transmitters:
        delta = 0.04
        if tid == "dopamine":
            brain.modulators.dopamine = float(np.clip(brain.modulators.dopamine + delta, 0, 1))
        elif tid == "norepinephrine":
            brain.modulators.norepinephrine = float(np.clip(brain.modulators.norepinephrine + delta, 0, 1))
        elif tid == "acetylcholine":
            brain.modulators.acetylcholine = float(np.clip(brain.modulators.acetylcholine + delta, 0, 1))
        elif tid == "cortisol" and section.track == "clinical_neurology":
            brain.modulators.update(reward=0.05, stress=0.18, novelty=0.22, attention=0.5, sleep_pressure=0.08)
    brain.working_memory.push(
        label=f"estudio: {section.title[:40]}",
        modality="document",
        room=brain.world.current_room(),
        goal=f"{section.track}:{section.key}",
        tags=[section.track, section.key],
    )
    brain.thoughts.inject_fragment(section.track, f"{section.n}. {section.title}", 0.7)
    brain.atlas.glia.astrocyte_tone = float(np.clip(brain.atlas.glia.astrocyte_tone + 0.03, 0, 1))


def study_section(
    brain: InfantApeBrain,
    state: TrackState,
    section: TrackSection,
    *,
    source: str,
    steps: int = 30,
    sleep: bool = False,
) -> dict[str, Any]:
    from .learning_hub import LearningEvent

    apply_track_effects(brain, section)
    prefix = "💤 " if sleep else ""
    icon = {"clinical_neurology": "🏥", "biopsych": "🧬", "infant_brain": "🧒"}.get(section.track, "📚")
    content = section.teaching
    if section.library_path:
        from .library import read_book
        from .text_extract import extract_plain_text

        try:
            data, fn = read_book(section.library_path)
            extracted = extract_plain_text(data, fn)
            if extracted.strip():
                content = f"{section.title}\n\n{extracted[:6000]}"
        except OSError:
            pass
    lr = brain.learning_hub.learn(
        brain,
        LearningEvent(
            source=source,
            label=f"{prefix}{icon} {section.title}",
            content=content[:8000],
            modality="text",
            tags=[*section.all_tags, "sleep_study" if sleep else "awake"],
            agents=["nexo"],
            steps_per_repeat=steps,
        ),
    )
    state.mark_studied(section.key)
    return {"section": section.to_dict(done=True), "learning": lr, "track": state.track_name}


def get_section(sections: tuple[TrackSection, ...], key: str | None = None) -> TrackSection | None:
    if not key:
        return None
    for s in sections:
        if s.key == key:
            return s
    return None
