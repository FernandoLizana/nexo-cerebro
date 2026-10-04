"""
Estudio autónomo durante el sueño — Nexo aprende «mientras duerme».

- Corre en fase REM y en worker background nocturno.
- Puede repasar currículo, Brain Facts, anatomía o buscar en la web (HTTP).
- **No** escribe ``choice_key`` ni elige acciones de vigilia (agency intacto).
"""

from __future__ import annotations

import json
import os
import random
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from .experiment_flags import get_flags
from .learning_hub import LearningEvent
from .sleep_architecture import _fit_sensory_pattern

if TYPE_CHECKING:
    from .mind import InfantApeBrain

SLEEP_STEPS_SCALE = 0.38
MAX_HISTORY = 48


@dataclass
class SleepStudyEntry:
    kind: str
    title: str
    query: str = ""
    snippet: str = ""
    phase: str = "rem"
    provider: str = ""
    remembered: bool = False
    time_ms: int = 0
    source: str = "sleep_rem"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "title": self.title,
            "query": self.query,
            "snippet": self.snippet[:160],
            "phase": self.phase,
            "provider": self.provider,
            "remembered": self.remembered,
            "time_ms": self.time_ms,
            "source": self.source,
            "icon": _icon_for(self.kind),
            "label": _label_for(self),
        }


def _icon_for(kind: str) -> str:
    return {
        "web": "🔍",
        "curriculum": "📚",
        "brain_facts": "📖",
        "anatomy": "🦴",
        "clinical": "🏥",
        "biopsych": "🧬",
        "infant_brain": "🧒",
        "library": "📂",
        "repaso": "🌙",
    }.get(kind, "💤")


def _label_for(entry: SleepStudyEntry) -> str:
    if entry.kind == "web":
        q = entry.query or entry.title
        return f"💤 búsqueda: {q[:56]}"
    if entry.kind == "repaso":
        return f"💤 repaso: {entry.title[:56]}"
    return f"💤 estudio: {entry.title[:56]}"


@dataclass
class SleepStudyLog:
    entries: list[dict[str, Any]] = field(default_factory=list)
    total_sessions: int = 0
    total_actions: int = 0
    last_action: dict[str, Any] | None = None
    background_ticks: int = 0

    def append(self, entry: SleepStudyEntry) -> dict[str, Any]:
        row = entry.to_dict()
        self.entries.insert(0, row)
        self.entries = self.entries[:MAX_HISTORY]
        self.total_actions += 1
        self.last_action = row
        return row

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": self.entries[:20],
            "history": self.entries[:MAX_HISTORY],
            "total_sessions": self.total_sessions,
            "total_actions": self.total_actions,
            "background_ticks": self.background_ticks,
            "last_action": self.last_action,
            "enabled": True,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> SleepStudyLog:
        if not data:
            return cls()
        return cls(
            entries=list(data.get("history") or data.get("entries") or [])[:MAX_HISTORY],
            total_sessions=int(data.get("total_sessions") or 0),
            total_actions=int(data.get("total_actions") or 0),
            last_action=data.get("last_action"),
            background_ticks=int(data.get("background_ticks") or 0),
        )

    def save(self, base_dir: Path) -> None:
        path = Path(base_dir) / "sleep_study_log.json"
        payload = {
            "history": self.entries,
            "total_sessions": self.total_sessions,
            "total_actions": self.total_actions,
            "background_ticks": self.background_ticks,
            "last_action": self.last_action,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, base_dir: Path) -> SleepStudyLog:
        path = Path(base_dir) / "sleep_study_log.json"
        if not path.exists():
            return cls()
        try:
            return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            return cls()


class SleepStudyEngine:
    """Motor de estudio offline / nocturno."""

    def __init__(self) -> None:
        self.log = SleepStudyLog()
        self._rng = random.Random()

    def attach_brain(self, brain: InfantApeBrain) -> None:
        sd = getattr(brain, "state_dir", None) or brain.persistence.base_dir
        self.log = SleepStudyLog.load(sd)

    def save(self, brain: InfantApeBrain) -> None:
        sd = getattr(brain, "state_dir", None) or brain.persistence.base_dir
        self.log.save(sd)

    def enabled(self, brain: InfantApeBrain) -> bool:
        return bool(get_flags(brain).enable_sleep_study)

    def web_allowed(self, brain: InfantApeBrain) -> bool:
        flags = get_flags(brain)
        if not flags.enable_sleep_study:
            return False
        if not flags.enable_sleep_web:
            return False
        return os.environ.get("CEREBRO_SLEEP_WEB", "1").strip().lower() not in ("0", "false", "off", "no")

    def maybe_study_during_rem(
        self,
        brain: InfantApeBrain,
        *,
        cycle: int,
        phase: str = "rem",
    ) -> dict[str, Any] | None:
        if not self.enabled(brain):
            return None
        if cycle % 2 == 0 and self._rng.random() > 0.55:
            return None
        return self._run_one_action(brain, phase=phase, source="sleep_rem")

    def run_background_pass(self, brain: InfantApeBrain) -> dict[str, Any] | None:
        if not self.enabled(brain):
            return None
        amb = brain.world.ambient()
        hour = int(amb.get("hour", 12))
        at_night = amb.get("phase") == "night" or hour >= 22 or hour < 6
        sleepy = brain.brainstem.sleep_pressure > 0.48
        if not (at_night or sleepy):
            return None
        if self._rng.random() > 0.72:
            return None
        self.log.background_ticks += 1
        return self._run_one_action(brain, phase="background", source="sleep_background")

    def run_sleep_session(self, brain: InfantApeBrain, *, max_actions: int = 2) -> dict[str, Any]:
        if not self.enabled(brain):
            return {"actions": [], "count": 0}
        self.log.total_sessions += 1
        actions: list[dict] = []
        for _ in range(max(1, min(max_actions, 3))):
            row = self._run_one_action(brain, phase="rem", source="sleep_session")
            if row:
                actions.append(row)
        self.save(brain)
        return {"actions": actions, "count": len(actions)}

    def _run_one_action(
        self,
        brain: InfantApeBrain,
        *,
        phase: str,
        source: str,
    ) -> dict[str, Any] | None:
        weights = self._action_weights(brain)
        kind = self._pick_kind(weights)
        handler = {
            "web": self._study_web,
            "curriculum": self._study_curriculum,
            "brain_facts": self._study_brain_facts,
            "anatomy": self._study_anatomy,
            "clinical": self._study_clinical,
            "biopsych": self._study_biopsych,
            "infant_brain": self._study_infant,
            "library": self._study_library,
            "node_shelf": self._study_nodes,
            "repaso": self._study_repaso,
        }.get(kind, self._study_repaso)
        try:
            entry = handler(brain, phase=phase, source=source)
        except (OSError, ValueError, TypeError, KeyError, urllib.error.URLError, TimeoutError):
            return None
        if not entry:
            return None
        row = self.log.append(entry)
        brain._learning_log.insert(0, row["label"])
        brain._learning_log = brain._learning_log[:12]
        brain.thoughts.inject_fragment("sleep_study", row["title"][:48], 0.55)
        self.save(brain)
        return row

    def _action_weights(self, brain: InfantApeBrain) -> dict[str, float]:
        from .behavior_integration import sleep_study_weights

        w = sleep_study_weights(brain)
        if self.web_allowed(brain):
            w["web"] = max(w.get("web", 0.05), 0.14)
        else:
            w["web"] = 0.0
        if brain.curriculum.suggest_next() is None:
            w["curriculum"] = 0.04
            w["repaso"] = w.get("repaso", 0.16) + 0.08
        from .library import list_books

        if not list_books():
            w["library"] = 0.0
        from .node_offerings import unread_offerings

        if unread_offerings():
            w["node_shelf"] = 0.55
        return w

    def _pick_kind(self, weights: dict[str, float]) -> str:
        items = [(k, v) for k, v in weights.items() if v > 0]
        if not items:
            return "repaso"
        keys, vals = zip(*items)
        return self._rng.choices(keys, weights=vals, k=1)[0]

    def _sleep_learn(
        self,
        brain: InfantApeBrain,
        event: LearningEvent,
        *,
        steps_scale: float = SLEEP_STEPS_SCALE,
    ) -> dict:
        scaled = LearningEvent(
            source=event.source,
            label=event.label,
            content=event.content,
            modality=event.modality,
            tags=[*event.tags, "sleep_study", "offline"],
            agents=["nexo"],
            steps_per_repeat=max(6, int(event.steps_per_repeat * steps_scale)),
        )
        return brain.learning_hub.learn(brain, scaled)

    def _study_web(
        self,
        brain: InfantApeBrain,
        *,
        phase: str,
        source: str,
    ) -> SleepStudyEntry | None:
        if not self.web_allowed(brain):
            return self._study_repaso(brain, phase=phase, source=source)
        from .web_fetch import fetch_page_text
        from .web_search import format_for_learning, search as web_search_fn

        lctx = brain._language_context(ep=brain._last_ep or {}, mode="sleep")
        query, _ = brain.language.suggest_web_query(lctx)
        if not query:
            section = brain.curriculum.suggest_next() or brain.brain_facts.suggest_next()
            if section and hasattr(section, "title"):
                query = f"neurociencia {section.title[:40]}"
            else:
                query = "hipocampo memoria sueño consolidación"
        payload = web_search_fn(query, limit=4)
        results = payload.get("results") or []
        if not results:
            return self._study_repaso(brain, phase=phase, source=source)
        top = results[0]
        content = format_for_learning(payload)
        page = fetch_page_text(str(top.get("url", "")))
        if page:
            content = content + "\n\nExtracto nocturno:\n" + page[:900]
        lr = self._sleep_learn(
            brain,
            LearningEvent(
                source="google",
                label=f"💤 Web: {top.get('title', query)[:50]}",
                content=content,
                modality="text",
                tags=["world", "web", "sleep", f"q:{query[:18]}"],
                steps_per_repeat=28,
            ),
        )
        remembered = bool(lr.get("learned", {}).get("remembered", False))
        return SleepStudyEntry(
            kind="web",
            title=str(top.get("title", query))[:80],
            query=query,
            snippet=str(top.get("snippet", ""))[:140],
            phase=phase,
            provider=str(payload.get("provider", "web")),
            remembered=remembered,
            time_ms=int(brain.cortex.time_ms),
            source=source,
        )

    def _study_curriculum(
        self,
        brain: InfantApeBrain,
        *,
        phase: str,
        source: str,
    ) -> SleepStudyEntry | None:
        from .curriculum import get_section, study_section

        section = brain.curriculum.suggest_next()
        if not section:
            return self._study_repaso(brain, phase=phase, source=source)
        content = f"[sueño REM]\n{section.title}\n\n{section.teaching[:1200]}"
        lr = self._sleep_learn(
            brain,
            LearningEvent(
                source="curriculum",
                label=f"💤 {section.title}",
                content=content,
                modality="text",
                tags=[*section.tags, "sleep"],
                steps_per_repeat=22,
            ),
        )
        brain.curriculum.mark_studied(section.key)
        remembered = bool(lr.get("learned", {}).get("remembered", False))
        return SleepStudyEntry(
            kind="curriculum",
            title=section.title,
            snippet=section.teaching[:120],
            phase=phase,
            remembered=remembered,
            time_ms=int(brain.cortex.time_ms),
            source=source,
        )

    def _study_brain_facts(
        self,
        brain: InfantApeBrain,
        *,
        phase: str,
        source: str,
    ) -> SleepStudyEntry | None:
        from .brain_facts import get_chapter, study_chapter

        chapter = brain.brain_facts.suggest_next()
        if not chapter:
            return self._study_repaso(brain, phase=phase, source=source)
        content = f"[sueño REM]\n{chapter.title}\n\n{chapter.teaching[:1400]}"
        lr = self._sleep_learn(
            brain,
            LearningEvent(
                source="brain_facts",
                label=f"💤 {chapter.title}",
                content=content,
                modality="text",
                tags=["brain_facts", chapter.key, "sleep"],
                steps_per_repeat=24,
            ),
        )
        brain.brain_facts.mark_studied(chapter.key)
        remembered = bool(lr.get("learned", {}).get("remembered", False))
        return SleepStudyEntry(
            kind="brain_facts",
            title=chapter.title,
            snippet=chapter.teaching[:120],
            phase=phase,
            remembered=remembered,
            time_ms=int(brain.cortex.time_ms),
            source=source,
        )

    def _study_anatomy(
        self,
        brain: InfantApeBrain,
        *,
        phase: str,
        source: str,
    ) -> SleepStudyEntry | None:
        from .anatomy_curriculum import study_anatomy_section

        section = brain.anatomy.suggest_next()
        if not section:
            return self._study_repaso(brain, phase=phase, source=source)
        result = study_anatomy_section(brain, section)
        lr = result.get("learning", {})
        remembered = bool(lr.get("learned", {}).get("remembered", False))
        sec = result.get("section") or section.to_dict(done=True)
        title = str(sec.get("title", section.title))
        snippet = section.teaching[:120]
        return SleepStudyEntry(
            kind="anatomy",
            title=title,
            snippet=snippet,
            phase=phase,
            remembered=remembered,
            time_ms=int(brain.cortex.time_ms),
            source=source,
        )

    def _study_clinical(
        self,
        brain: InfantApeBrain,
        *,
        phase: str,
        source: str,
    ) -> SleepStudyEntry | None:
        from .clinical_neurology import study_clinical_section

        section = brain.clinical_neurology.suggest_next()
        if not section:
            return self._study_repaso(brain, phase=phase, source=source)
        result = study_clinical_section(brain, section, sleep=True)
        lr = result.get("learning", {})
        remembered = bool(lr.get("learned", {}).get("remembered", False))
        return SleepStudyEntry(
            kind="clinical",
            title=section.title,
            snippet=section.teaching[:120],
            phase=phase,
            remembered=remembered,
            time_ms=int(brain.cortex.time_ms),
            source=source,
        )

    def _study_biopsych(
        self,
        brain: InfantApeBrain,
        *,
        phase: str,
        source: str,
    ) -> SleepStudyEntry | None:
        from .biopsych_curriculum import study_biopsych_section

        section = brain.biopsych.suggest_next()
        if not section:
            return self._study_repaso(brain, phase=phase, source=source)
        result = study_biopsych_section(brain, section, sleep=True)
        lr = result.get("learning", {})
        remembered = bool(lr.get("learned", {}).get("remembered", False))
        return SleepStudyEntry(
            kind="biopsych",
            title=section.title,
            snippet=section.teaching[:120],
            phase=phase,
            remembered=remembered,
            time_ms=int(brain.cortex.time_ms),
            source=source,
        )

    def _study_infant(
        self,
        brain: InfantApeBrain,
        *,
        phase: str,
        source: str,
    ) -> SleepStudyEntry | None:
        from .infant_brain_curriculum import study_infant_section

        section = brain.infant_brain.suggest_next()
        if not section:
            return self._study_repaso(brain, phase=phase, source=source)
        result = study_infant_section(brain, section, sleep=True)
        lr = result.get("learning", {})
        remembered = bool(lr.get("learned", {}).get("remembered", False))
        return SleepStudyEntry(
            kind="infant_brain",
            title=section.title,
            snippet=section.teaching[:120],
            phase=phase,
            remembered=remembered,
            time_ms=int(brain.cortex.time_ms),
            source=source,
        )

    def _study_nodes(
        self,
        brain: InfantApeBrain,
        *,
        phase: str,
        source: str,
    ) -> SleepStudyEntry | None:
        from .node_offerings import take_offering

        item = take_offering()
        if not item:
            return self._study_repaso(brain, phase=phase, source=source)
        from .collective_capacity import learn_offering

        learned = learn_offering(brain, item, via="sueño")
        lr = learned["learned"]
        text = str(item.get("text") or "")
        name = str(item.get("name") or "material")
        remembered = bool(lr.get("learned", {}).get("remembered", False))
        return SleepStudyEntry(
            kind="node_shelf",
            title=name,
            snippet=text[:120] or "sin texto",
            phase=phase,
            remembered=remembered,
            time_ms=int(brain.cortex.time_ms),
            source=source,
        )

    def _study_library(
        self,
        brain: InfantApeBrain,
        *,
        phase: str,
        source: str,
    ) -> SleepStudyEntry | None:
        from .library import list_books, read_book
        from .text_extract import extract_plain_text

        books = list_books()
        if not books:
            return self._study_repaso(brain, phase=phase, source=source)
        book = self._rng.choice(books)
        rel = str(book.get("path", ""))
        name = str(book.get("name", rel))
        try:
            data, fn = read_book(rel)
            text = extract_plain_text(data, fn)
        except OSError:
            return self._study_repaso(brain, phase=phase, source=source)
        if not text.strip():
            text = f"Libro en biblioteca: {name}. (PDF escaneado — texto pendiente de OCR.)"
        content = f"[sueño REM · biblioteca]\n{name}\n\n{text[:5000]}"
        lr = self._sleep_learn(
            brain,
            LearningEvent(
                source="library",
                label=f"💤 📂 {name[:48]}",
                content=content,
                modality="text",
                tags=["library", "sleep", f"book:{rel[:24]}"],
                steps_per_repeat=18,
            ),
        )
        remembered = bool(lr.get("learned", {}).get("remembered", False))
        return SleepStudyEntry(
            kind="library",
            title=name,
            snippet=text[:120] if text else "sin texto extraíble",
            phase=phase,
            remembered=remembered,
            time_ms=int(brain.cortex.time_ms),
            source=source,
        )

    def _study_repaso(
        self,
        brain: InfantApeBrain,
        *,
        phase: str,
        source: str,
    ) -> SleepStudyEntry | None:
        mem = brain.hippocampus.sample_for_replay(
            sleep_pressure=max(0.5, brain.brainstem.sleep_pressure),
            modulators=brain.modulators,
            sleep_phase="rem",
            replay_mode="selective",
        )
        if mem is None:
            from .curriculum import SECTIONS, get_section

            done = [k for k in brain.curriculum.completed if k in {s.key for s in SECTIONS}]
            if done:
                sec = get_section(key=self._rng.choice(done))
                if sec:
                    content = f"Repaso nocturno: {sec.title}\n{sec.teaching[:800]}"
                    title = sec.title
                else:
                    content = "Consolidación silenciosa de recuerdos recientes."
                    title = "eco de memoria"
            else:
                content = "Sueño profundo — sin episodio explícito que repasar."
                title = "silencio hipocampal"
        else:
            label = str(mem.get("label", "recuerdo"))[:80]
            tags = mem.get("tags") or []
            content = f"Repaso nocturno: {label}\nEtiquetas: {', '.join(str(t) for t in tags[:6])}"
            title = label
            raw = mem.get("pattern", mem.get("sensory"))
            if raw is not None:
                sensory = _fit_sensory_pattern(raw, brain.n_sensory)
                brain._simulate(sensory, total_steps=14)

        lr = self._sleep_learn(
            brain,
            LearningEvent(
                source="repaso",
                label=f"💤 repaso: {title[:50]}",
                content=content,
                modality="text",
                tags=["sleep", "repaso", "offline"],
                steps_per_repeat=12,
            ),
        )
        remembered = bool(lr.get("learned", {}).get("remembered", False))
        return SleepStudyEntry(
            kind="repaso",
            title=title,
            snippet=content[:120],
            phase=phase,
            remembered=remembered,
            time_ms=int(brain.cortex.time_ms),
            source=source,
        )

    def to_dict(self) -> dict[str, Any]:
        return self.log.to_dict()

