"""
Currículo neurocientífico integrado — 46 lecciones que Nexo estudia y simula.

Cada sección codifica contenido vía LearningHub, marca progreso en memoria
y aplica sesgos a moduladores / química / atlas según anatomía y NTs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain

_CURRICULUM_PATH = Path(__file__).resolve().parent.parent / "data" / "curriculum" / "sections.json"


@dataclass(frozen=True)
class CurriculumSection:
    n: int
    key: str
    title: str
    teaching: str
    anatomy: tuple[str, ...] = ()
    transmitters: tuple[str, ...] = ()
    valence: float = 0.12
    arousal: float = 0.38
    novelty: float = 0.55

    @property
    def tags(self) -> list[str]:
        return [
            "curriculum",
            f"section:{self.n:02d}",
            f"topic:{self.key}",
            *[f"anatomy:{a}" for a in self.anatomy[:4]],
            *[f"nt:{t}" for t in self.transmitters[:3]],
        ]

    def to_dict(self, *, done: bool = False) -> dict[str, Any]:
        return {
            "n": self.n,
            "key": self.key,
            "title": self.title,
            "anatomy": list(self.anatomy),
            "transmitters": list(self.transmitters),
            "done": done,
            "preview": self.teaching[:120] + ("…" if len(self.teaching) > 120 else ""),
        }


def _load_sections() -> tuple[CurriculumSection, ...]:
    raw = json.loads(_CURRICULUM_PATH.read_text(encoding="utf-8"))
    out: list[CurriculumSection] = []
    for item in raw:
        out.append(
            CurriculumSection(
                n=int(item["n"]),
                key=str(item["key"]),
                title=str(item["title"]),
                teaching=str(item["teaching"]),
                anatomy=tuple(item.get("anatomy") or ()),
                transmitters=tuple(item.get("transmitters") or ()),
            )
        )
    return tuple(sorted(out, key=lambda s: s.n))


SECTIONS: tuple[CurriculumSection, ...] = _load_sections()
SECTION_BY_KEY: dict[str, CurriculumSection] = {s.key: s for s in SECTIONS}


@dataclass
class CurriculumState:
    """Progreso de estudio autónomo / guiado."""

    completed: set[str] = field(default_factory=set)
    current_key: str | None = None
    last_key: str | None = None
    study_count: int = 0
    focus_ticks: int = 0
    focus_anatomy: list[str] = field(default_factory=list)

    def mark_studied(self, key: str) -> None:
        self.completed.add(key)
        self.last_key = key
        self.current_key = key
        self.study_count += 1
        sec = SECTION_BY_KEY.get(key)
        if sec:
            self.focus_anatomy = list(sec.anatomy[:6])
            self.focus_ticks = 48

    def suggest_next(self) -> CurriculumSection | None:
        for sec in SECTIONS:
            if sec.key not in self.completed:
                return sec
        return SECTIONS[0] if SECTIONS else None

    def progress_ratio(self) -> float:
        if not SECTIONS:
            return 0.0
        return len(self.completed) / len(SECTIONS)

    def tick_focus(self) -> None:
        if self.focus_ticks > 0:
            self.focus_ticks -= 1
        if self.focus_ticks <= 0:
            self.focus_anatomy = []

    def to_dict(self) -> dict[str, Any]:
        current = SECTION_BY_KEY.get(self.current_key) if self.current_key else None
        last = SECTION_BY_KEY.get(self.last_key) if self.last_key else None
        return {
            "total": len(SECTIONS),
            "completed": len(self.completed),
            "progress": round(self.progress_ratio(), 3),
            "current_key": self.current_key,
            "current_title": current.title if current else None,
            "last_key": self.last_key,
            "last_title": last.title if last else None,
            "study_count": self.study_count,
            "focus_ticks": self.focus_ticks,
            "focus_anatomy": list(self.focus_anatomy),
            "sections": [s.to_dict(done=s.key in self.completed) for s in SECTIONS],
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> CurriculumState:
        if not data:
            return cls()
        completed = data.get("completed")
        if completed is None and data.get("sections"):
            completed = [s["key"] for s in data["sections"] if s.get("done")]
        st = cls(
            completed=set(completed or []),
            current_key=data.get("current_key"),
            last_key=data.get("last_key"),
            study_count=int(data.get("study_count") or 0),
            focus_ticks=int(data.get("focus_ticks") or 0),
            focus_anatomy=list(data.get("focus_anatomy") or []),
        )
        return st


def apply_study_effects(brain: InfantApeBrain, section: CurriculumSection) -> None:
    """Sesgo neuroquímico y atencional al estudiar una lección."""
    brain.affect.process_stimulus(
        valence=section.valence,
        arousal=section.arousal,
        novelty=section.novelty,
        pain=0.0,
        social_bond=0.08,
        attention=0.55,
        surprise=0.15,
    )
    brain.affect.step()
    brain.affect.sync_modulators(brain.modulators)
    brain.affect.sync_hypothalamus(
        brain.hypothalamus,
        valence=section.valence,
        arousal=section.arousal,
    )

    nt_boost = {
        "dopamine": 0.06,
        "serotonin": 0.04,
        "norepinephrine": 0.05,
        "acetylcholine": 0.08,
        "gaba": 0.03,
        "glutamate": 0.06,
        "oxytocin": 0.04,
        "cortisol": -0.02,
    }
    for tid in section.transmitters:
        delta = nt_boost.get(tid, 0.03)
        if tid == "dopamine":
            brain.modulators.dopamine = float(np.clip(brain.modulators.dopamine + delta, 0, 1))
        elif tid == "serotonin":
            brain.modulators.serotonin = float(np.clip(brain.modulators.serotonin + delta, 0, 1))
        elif tid == "norepinephrine":
            brain.modulators.norepinephrine = float(np.clip(brain.modulators.norepinephrine + delta, 0, 1))
        elif tid == "acetylcholine":
            brain.modulators.acetylcholine = float(np.clip(brain.modulators.acetylcholine + delta, 0, 1))
        elif tid == "gaba":
            brain.modulators.gaba_tone = float(np.clip(brain.modulators.gaba_tone + delta, 0, 1))
        elif tid == "glutamate":
            brain.modulators.glutamate_drive = float(np.clip(brain.modulators.glutamate_drive + delta, 0, 1))
        elif tid == "oxytocin":
            brain.modulators.oxytocin = float(np.clip(brain.modulators.oxytocin + delta, 0, 1))
        elif tid == "cortisol":
            brain.modulators.update(reward=0.1, stress=0.12, novelty=0.2, attention=0.4, sleep_pressure=0.2, social_bond=0.1)

    brain.working_memory.push(
        label=f"estudio: {section.title[:40]}",
        modality="document",
        room=brain.world.current_room(),
        goal=f"curriculum:{section.key}",
        tags=["curriculum", section.key],
    )
    brain.thoughts.inject_fragment("curriculum", f"{section.n}. {section.title}", 0.72)
    brain.atlas.glia.astrocyte_tone = float(
        np.clip(brain.atlas.glia.astrocyte_tone + 0.04, 0, 1)
    )


def anatomy_focus_boost(structure_id: str, base: float, focus: list[str]) -> float:
    if structure_id in focus:
        return float(np.clip(base + 0.22, 0, 1))
    return base


def study_section(brain: InfantApeBrain, section: CurriculumSection) -> dict[str, Any]:
    """Aprendizaje episódico de una lección — llamado desde mind."""
    from .learning_hub import LearningEvent

    apply_study_effects(brain, section)
    content = f"{section.title}\n\n{section.teaching}"
    lr = brain.learning_hub.learn(
        brain,
        LearningEvent(
            source="curriculum",
            label=f"📚 {section.title}",
            content=content,
            modality="text",
            tags=section.tags,
            agents=brain._learning_agents(50),
            steps_per_repeat=34,
        ),
    )
    brain.curriculum.mark_studied(section.key)
    return {"section": section.to_dict(done=True), "learning": lr}


def get_section(key: str | None = None, n: int | None = None) -> CurriculumSection | None:
    if key and key in SECTION_BY_KEY:
        return SECTION_BY_KEY[key]
    if n is not None:
        for s in SECTIONS:
            if s.n == n:
                return s
    return None
