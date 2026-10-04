"""
Dinámica de memoria — Bloque E (items 45–56).

Olvido, interferencia, contexto rico, flashbulb, línea autobiográfica.
No escribe choice_key.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .consolidation import forgetting_retention
from .experiment_flags import get_flags


@dataclass
class MemoryInterferenceTracker:
    """Interferencia proactiva/retroactiva entre codificaciones cercanas."""

    recent_labels: list[str] = field(default_factory=list)
    proactive: float = 0.0
    retroactive: float = 0.0

    def note_encode(self, label: str) -> None:
        self.recent_labels.insert(0, label[:48])
        self.recent_labels = self.recent_labels[:12]
        overlap = len(set(self.recent_labels)) / max(len(self.recent_labels), 1)
        self.proactive = float(np.clip(1.0 - overlap + 0.15, 0, 0.65))
        self.retroactive = float(np.clip(len(self.recent_labels) / 12.0 * 0.4, 0, 0.5))

    def recall_penalty(self) -> float:
        return float(np.clip(self.proactive * 0.08 + self.retroactive * 0.06, 0, 0.12))


@dataclass
class FlashbulbRegistry:
    """Recuerdos de alto arousal — recall privilegiado."""

    entries: dict[str, dict[str, Any]] = field(default_factory=dict)

    def is_flashbulb(self, key: str) -> bool:
        return key in self.entries

    def mark(
        self,
        *,
        key: str,
        label: str,
        valence: float,
        arousal: float,
        tags: list[str] | None = None,
    ) -> bool:
        if abs(valence) < 0.45 or arousal < 0.55:
            return False
        self.entries[key] = {
            "label": label[:60],
            "valence": round(valence, 3),
            "arousal": round(arousal, 3),
            "ts": time.time(),
            "tags": list(tags or [])[:6],
        }
        if len(self.entries) > 32:
            oldest = min(self.entries, key=lambda k: self.entries[k]["ts"])
            del self.entries[oldest]
        return True

    def replay_boost(self, key: str) -> float:
        if key not in self.entries:
            return 0.0
        e = self.entries[key]
        return float(np.clip(0.35 + abs(e["valence"]) * 0.3 + e["arousal"] * 0.25, 0.2, 0.85))


@dataclass
class AutobiographicalTimeline:
    """Línea temporal del yo — eventos narrativos significativos."""

    events: list[dict[str, Any]] = field(default_factory=list)

    def add(
        self,
        *,
        label: str,
        room: str,
        tick: int,
        valence: float = 0.0,
        tags: list[str] | None = None,
    ) -> None:
        entry = {
            "label": label[:72],
            "room": room,
            "tick": tick,
            "valence": round(valence, 3),
            "tags": list(tags or [])[:4],
        }
        if self.events and self.events[0]["label"] == entry["label"]:
            return
        self.events.insert(0, entry)
        self.events = self.events[:24]

    def narrative_lines(self) -> list[str]:
        return [f"{e['label']} ({e['room']})" for e in self.events[:8]]


@dataclass
class MemoryDynamicsStack:
    interference: MemoryInterferenceTracker = field(default_factory=MemoryInterferenceTracker)
    flashbulb: FlashbulbRegistry = field(default_factory=FlashbulbRegistry)
    autobiography: AutobiographicalTimeline = field(default_factory=AutobiographicalTimeline)
    last_recall_meta: dict[str, Any] = field(default_factory=dict)

    def on_encode(
        self,
        brain,
        memory: dict,
        *,
        label: str,
        valence: float,
        arousal: float,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        flags = get_flags(brain)
        if not flags.enable_memory_dynamics:
            return {}
        self.interference.note_encode(label)
        out: dict[str, Any] = {}
        key = str(memory.get("key", ""))
        if flags.enable_flashbulb_memory:
            if self.flashbulb.mark(key=key, label=label, valence=valence, arousal=arousal, tags=tags):
                out["flashbulb"] = True
                if tags is not None and "flashbulb" not in tags:
                    tags.append("flashbulb")
        if flags.enable_autobiographical_timeline:
            if abs(valence) > 0.3 or arousal > 0.5 or "flashbulb" in (tags or []):
                self.autobiography.add(
                    label=label,
                    room=brain.world.current_room(),
                    tick=int(brain.lifecycle.age_ticks),
                    valence=valence,
                    tags=tags,
                )
                brain.consciousness.self_model.narrative = self.autobiography.narrative_lines()
        return out

    def adjust_recall_score(self, brain, mem: dict, score: float) -> float:
        flags = get_flags(brain)
        if not flags.enable_memory_dynamics:
            return score
        adjusted = score
        if flags.enable_forgetting_curve:
            updated = float(mem.get("updated_at", time.time()))
            age_h = (time.time() - updated) / 3600.0
            emotional = abs(float(mem.get("valence", 0))) + float(mem.get("arousal", 0)) * 0.5
            if self.flashbulb.is_flashbulb(str(mem.get("key", ""))):
                emotional = max(emotional, 0.75)
            adjusted *= forgetting_retention(age_hours=age_h, emotional=emotional)
        if flags.enable_memory_interference:
            adjusted -= self.interference.recall_penalty()
        if (
            flags.enable_lifecycle_dynamics
            and flags.enable_cognitive_aging
            and hasattr(brain, "lifecycle_dynamics")
        ):
            adjusted -= brain.lifecycle_dynamics.recall_aging_penalty
        if flags.enable_flashbulb_memory:
            boost = self.flashbulb.replay_boost(str(mem.get("key", "")))
            adjusted += boost * 0.12
        return float(np.clip(adjusted, 0, 1.2))

    def post_recall(self, brain, result: dict | None) -> dict | None:
        if not result or not get_flags(brain).enable_memory_dynamics:
            return result
        score = float(result.get("similarity", 0))
        mem_key = str(result.get("key", ""))
        self.last_recall_meta = {"similarity_raw": score, "key": mem_key}

        if get_flags(brain).enable_source_confusion:
            threshold = brain.memory_store.recall_threshold
            if threshold <= score <= threshold + 0.14:
                confusable = self._find_confusable(brain, result)
                if confusable:
                    result = dict(result)
                    result["label"] = confusable.get("label", result.get("label"))
                    result["source_confused"] = True
                    result["confused_with"] = confusable.get("key", "")
                    self.last_recall_meta["source_confused"] = True

        return result

    def _find_confusable(self, brain, result: dict) -> dict | None:
        room = result.get("room", "")
        label = str(result.get("label", "")).lower()
        candidates = brain.hippocampus.list_recent(8)
        for c in candidates:
            if c.get("key") == result.get("key"):
                continue
            if c.get("room") == room and label[:4] == str(c.get("label", "")).lower()[:4]:
                return c
        return None

    def daytime_replay_threshold(self, brain, base: float) -> float:
        if not get_flags(brain).enable_memory_dynamics:
            return base
        if self.flashbulb.entries:
            return base - 0.08
        if brain.amygdala.arousal > 0.55:
            return base - 0.06
        return base

    def to_dict(self) -> dict[str, Any]:
        return {
            "interference": {
                "proactive": round(self.interference.proactive, 3),
                "retroactive": round(self.interference.retroactive, 3),
            },
            "flashbulb_count": len(self.flashbulb.entries),
            "flashbulb_recent": list(self.flashbulb.entries.values())[-3:],
            "autobiography": self.autobiography.events[:6],
            "last_recall": self.last_recall_meta,
        }
