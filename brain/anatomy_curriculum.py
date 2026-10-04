"""
Anatomía Humana 2022 (UCadiz) — corpus, progreso y estudio integrado con Nexo.

Morfología general, aparato locomotor, miembros superior e inferior.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain

MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "curriculum"
    / "anatomy_humana_2022_manifest.json"
)


@dataclass(frozen=True)
class AnatomySection:
    key: str
    title: str
    chapter: int
    page_start: int
    page_end: int
    anatomy: tuple[str, ...]
    teaching: str
    preview: str

    def to_dict(self, *, done: bool = False) -> dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "chapter": self.chapter,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "anatomy": list(self.anatomy),
            "done": done,
            "preview": self.preview,
        }


def _load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.is_file():
        return {"sections": [], "source": "missing"}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_sections() -> tuple[AnatomySection, ...]:
    data = _load_manifest()
    out: list[AnatomySection] = []
    for item in data.get("sections") or []:
        out.append(
            AnatomySection(
                key=str(item["key"]),
                title=str(item["title"]),
                chapter=int(item.get("chapter", 0)),
                page_start=int(item.get("page_start", 0)),
                page_end=int(item.get("page_end", 0)),
                anatomy=tuple(item.get("anatomy") or ()),
                teaching=str(item.get("text", ""))[:14000],
                preview=str(item.get("preview", ""))[:280],
            )
        )
    return tuple(out)


SECTIONS: tuple[AnatomySection, ...] = load_sections()
SECTION_BY_KEY: dict[str, AnatomySection] = {s.key: s for s in SECTIONS}


@dataclass
class AnatomyCorpus:
    completed: set[str] = field(default_factory=set)
    studied_order: list[str] = field(default_factory=list)
    current_key: str | None = None
    last_key: str | None = None
    study_count: int = 0
    focus_anatomy: list[str] = field(default_factory=list)
    focus_ticks: int = 0

    def suggest_next(self) -> AnatomySection | None:
        for sec in SECTIONS:
            if sec.key not in self.completed:
                return sec
        return SECTIONS[0] if SECTIONS else None

    def mark_studied(self, key: str) -> None:
        self.completed.add(key)
        self.studied_order.append(key)
        self.last_key = key
        self.current_key = key
        self.study_count += 1
        sec = SECTION_BY_KEY.get(key)
        if sec:
            self.focus_anatomy = list(sec.anatomy[:8])
            self.focus_ticks = 72

    def tick_focus(self) -> None:
        if self.focus_ticks > 0:
            self.focus_ticks -= 1
        if self.focus_ticks <= 0:
            self.focus_anatomy = []

    def progress_ratio(self) -> float:
        if not SECTIONS:
            return 0.0
        return len(self.completed) / len(SECTIONS)

    def to_dict(self) -> dict[str, Any]:
        data = _load_manifest()
        current = SECTION_BY_KEY.get(self.current_key) if self.current_key else None
        nxt = self.suggest_next()
        return {
            "source": data.get("source", "Anatomía Humana 2022 UCadiz"),
            "library_path": data.get("library_path"),
            "total_sections": len(SECTIONS),
            "completed": len(self.completed),
            "progress": round(self.progress_ratio(), 3),
            "study_count": self.study_count,
            "current": current.to_dict(done=current.key in self.completed) if current else None,
            "next": nxt.to_dict(done=False) if nxt else None,
            "focus_anatomy": self.focus_anatomy,
            "focus_ticks": self.focus_ticks,
            "sections": [
                SECTION_BY_KEY[k].to_dict(done=True)
                for k in self.studied_order[-6:]
                if k in SECTION_BY_KEY
            ],
            "pending": [
                s.to_dict(done=False)
                for s in SECTIONS
                if s.key not in self.completed
            ][:5],
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> AnatomyCorpus:
        if not data:
            return cls()
        return cls(
            completed=set(data.get("completed") or []),
            current_key=data.get("current_key"),
            last_key=data.get("last_key"),
            study_count=int(data.get("study_count") or 0),
            focus_anatomy=list(data.get("focus_anatomy") or []),
            focus_ticks=int(data.get("focus_ticks") or 0),
            studied_order=list(data.get("studied_order") or []),
        )


def apply_section_effects(brain: InfantApeBrain, section: AnatomySection) -> None:
    brain.affect.process_stimulus(
        valence=0.14,
        arousal=0.44,
        novelty=0.58,
        pain=brain.body.total_pain() * 0.15,
        social_bond=0.04,
        attention=0.58,
        surprise=0.18,
    )
    brain.affect.step()
    brain.affect.sync_modulators(brain.modulators)

    anatomy_nt = {
        "osteology": ("acetylcholine", 0.05),
        "arthrology": ("glutamate", 0.04),
        "myology": ("dopamine", 0.06),
        "nociception": ("norepinephrine", 0.05),
        "spinal": ("norepinephrine", 0.04),
        "locomotor": ("dopamine", 0.05),
        "brachial_plexus": ("acetylcholine", 0.05),
        "lumbosacral": ("acetylcholine", 0.05),
    }
    for anat in section.anatomy:
        tid, delta = anatomy_nt.get(anat, ("glutamate", 0.03))
        if tid == "dopamine":
            brain.modulators.dopamine = float(np.clip(brain.modulators.dopamine + delta, 0, 1))
        elif tid == "acetylcholine":
            brain.modulators.acetylcholine = float(np.clip(brain.modulators.acetylcholine + delta, 0, 1))
        elif tid == "norepinephrine":
            brain.modulators.norepinephrine = float(np.clip(brain.modulators.norepinephrine + delta, 0, 1))
        elif tid == "glutamate":
            brain.modulators.glutamate_drive = float(np.clip(brain.modulators.glutamate_drive + delta, 0, 1))

    brain.working_memory.push(
        label=f"Anatomía: {section.title[:36]}",
        modality="document",
        room=brain.world.current_room(),
        goal=f"anatomy:{section.key}",
        tags=["anatomy", section.key, *section.anatomy[:3]],
    )
    brain.thoughts.inject_fragment("anatomy", section.title, 0.72)


def study_anatomy_section(brain: InfantApeBrain, section: AnatomySection) -> dict[str, Any]:
    from .learning_hub import LearningEvent

    apply_section_effects(brain, section)
    content = f"{section.title}\n\n{section.teaching}"
    lr = brain.learning_hub.learn(
        brain,
        LearningEvent(
            source="anatomy",
            label=f"🦴 {section.title}",
            content=content,
            modality="text",
            tags=["anatomy", section.key, *[f"anat:{a}" for a in section.anatomy[:5]]],
            agents=brain._learning_agents(52),
            steps_per_repeat=40,
        ),
    )
    brain.anatomy.mark_studied(section.key)
    return {"section": section.to_dict(done=True), "learning": lr}


def get_section(key: str | None = None) -> AnatomySection | None:
    if key and key in SECTION_BY_KEY:
        return SECTION_BY_KEY[key]
    return None
