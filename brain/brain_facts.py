"""
Brain Facts 2018 (SfN) — corpus, progreso y estudio integrado con circuitos.

Carga el manifiesto extraído del PDF y conecta capítulos con módulos de Nexo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "data" / "curriculum" / "brain_facts_manifest.json"
BRAIN_FACTS_CHUNK = 1100
BRAIN_FACTS_MAX_CHUNKS = 14


@dataclass(frozen=True)
class BrainFactsChapter:
    key: str
    title: str
    page_start: int
    page_end: int
    modules: tuple[str, ...]
    teaching: str
    preview: str

    def to_dict(self, *, done: bool = False) -> dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "modules": list(self.modules),
            "done": done,
            "preview": self.preview,
        }


def _load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.is_file():
        return {"chapters": [], "core_concepts": [], "source": "missing"}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_chapters() -> tuple[BrainFactsChapter, ...]:
    data = _load_manifest()
    out: list[BrainFactsChapter] = []
    for item in data.get("chapters") or []:
        out.append(
            BrainFactsChapter(
                key=str(item["key"]),
                title=str(item["title"]),
                page_start=int(item.get("page_start", 0)),
                page_end=int(item.get("page_end", 0)),
                modules=tuple(item.get("modules") or ()),
                teaching=str(item.get("text", ""))[:14000],
                preview=str(item.get("preview", ""))[:280],
            )
        )
    return tuple(out)


CHAPTERS: tuple[BrainFactsChapter, ...] = load_chapters()
CHAPTER_BY_KEY: dict[str, BrainFactsChapter] = {c.key: c for c in CHAPTERS}


@dataclass
class BrainFactsCorpus:
    completed: set[str] = field(default_factory=set)
    studied_order: list[str] = field(default_factory=list)
    current_key: str | None = None
    last_key: str | None = None
    study_count: int = 0
    focus_modules: list[str] = field(default_factory=list)
    focus_ticks: int = 0
    core_concepts_done: set[str] = field(default_factory=set)

    def suggest_next(self) -> BrainFactsChapter | None:
        for ch in CHAPTERS:
            if ch.key not in self.completed:
                return ch
        return CHAPTERS[0] if CHAPTERS else None

    def mark_studied(self, key: str) -> None:
        self.completed.add(key)
        self.studied_order.append(key)
        self.last_key = key
        self.current_key = key
        self.study_count += 1
        ch = CHAPTER_BY_KEY.get(key)
        if ch:
            self.focus_modules = list(ch.modules[:8])
            self.focus_ticks = 64

    def tick_focus(self) -> None:
        if self.focus_ticks > 0:
            self.focus_ticks -= 1
        if self.focus_ticks <= 0:
            self.focus_modules = []

    def progress_ratio(self) -> float:
        if not CHAPTERS:
            return 0.0
        return len(self.completed) / len(CHAPTERS)

    def to_dict(self) -> dict[str, Any]:
        data = _load_manifest()
        current = CHAPTER_BY_KEY.get(self.current_key) if self.current_key else None
        nxt = self.suggest_next()
        return {
            "source": data.get("source", "Brain Facts 2018"),
            "library_path": data.get("library_path"),
            "total_chapters": len(CHAPTERS),
            "completed": len(self.completed),
            "progress": round(self.progress_ratio(), 3),
            "study_count": self.study_count,
            "current": current.to_dict(done=current.key in self.completed) if current else None,
            "next": nxt.to_dict(done=False) if nxt else None,
            "focus_modules": self.focus_modules,
            "focus_ticks": self.focus_ticks,
            "core_concepts": data.get("core_concepts") or [],
            "recent": [
                CHAPTER_BY_KEY[k].to_dict(done=True)
                for k in self.studied_order[-5:]
                if k in CHAPTER_BY_KEY
            ],
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> BrainFactsCorpus:
        if not data:
            return cls()
        return cls(
            completed=set(data.get("completed") or []),
            current_key=data.get("current_key"),
            last_key=data.get("last_key"),
            study_count=int(data.get("study_count") or 0),
            focus_modules=list(data.get("focus_modules") or []),
            focus_ticks=int(data.get("focus_ticks") or 0),
            studied_order=list(data.get("studied_order") or []),
            core_concepts_done=set(data.get("core_concepts_done") or []),
        )


def apply_chapter_effects(brain: InfantApeBrain, chapter: BrainFactsChapter) -> None:
    """Sesgos al estudiar un capítulo del libro."""
    brain.affect.process_stimulus(
        valence=0.18,
        arousal=0.42,
        novelty=0.62,
        pain=0.0,
        social_bond=0.05,
        attention=0.62,
        surprise=0.2,
    )
    brain.affect.step()
    brain.affect.sync_modulators(brain.modulators)

    module_nt = {
        "hippocampus": ("acetylcholine", 0.07),
        "amygdala": ("norepinephrine", 0.06),
        "basal_ganglia": ("dopamine", 0.07),
        "hypothalamus": ("cortisol", 0.0),
        "prefrontal": ("acetylcholine", 0.05),
        "thalamus": ("glutamate", 0.05),
    }
    for mod in chapter.modules:
        tid, delta = module_nt.get(mod, ("glutamate", 0.03))
        if tid == "dopamine":
            brain.modulators.dopamine = float(np.clip(brain.modulators.dopamine + delta, 0, 1))
        elif tid == "acetylcholine":
            brain.modulators.acetylcholine = float(np.clip(brain.modulators.acetylcholine + delta, 0, 1))
        elif tid == "norepinephrine":
            brain.modulators.norepinephrine = float(np.clip(brain.modulators.norepinephrine + delta, 0, 1))
        elif tid == "glutamate":
            brain.modulators.glutamate_drive = float(np.clip(brain.modulators.glutamate_drive + delta, 0, 1))

    brain.circuit_hub.studied_boost = float(np.clip(brain.circuit_hub.studied_boost + 0.08, 0, 0.5))
    brain.working_memory.push(
        label=f"Brain Facts: {chapter.title[:36]}",
        modality="document",
        room=brain.world.current_room(),
        goal=f"brain_facts:{chapter.key}",
        tags=["brain_facts", chapter.key, *chapter.modules[:3]],
    )
    brain.thoughts.inject_fragment("brain_facts", chapter.title, 0.78)


def study_chapter(brain: InfantApeBrain, chapter: BrainFactsChapter) -> dict[str, Any]:
    from .learning_hub import LearningEvent

    apply_chapter_effects(brain, chapter)
    content = f"{chapter.title}\n\n{chapter.teaching}"
    lr = brain.learning_hub.learn(
        brain,
        LearningEvent(
            source="brain_facts",
            label=f"📖 {chapter.title}",
            content=content,
            modality="text",
            tags=["brain_facts", chapter.key, *[f"mod:{m}" for m in chapter.modules[:5]]],
            agents=brain._learning_agents(52),
            steps_per_repeat=38,
        ),
    )
    brain.brain_facts.mark_studied(chapter.key)
    return {"chapter": chapter.to_dict(done=True), "learning": lr, "circuits": brain.circuit_hub.to_dict()}


def get_chapter(key: str | None = None) -> BrainFactsChapter | None:
    if key and key in CHAPTER_BY_KEY:
        return CHAPTER_BY_KEY[key]
    return None
