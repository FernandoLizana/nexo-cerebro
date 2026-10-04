"""
Sistemas de memoria tipados — episódica / semántica / procedimental (Brain Facts Ch.4).

- Episódica: hippocampus + EpisodicMemoryStore (existente)
- Semántica: conceptos estables (currículo, objetos, lugares)
- Procedimental: hábitos motores por contexto (ganglios basales)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from .deliberation import MOTOR_AFFINITY

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass
class SemanticConcept:
    key: str
    label: str
    strength: float = 0.5
    room: str = ""
    tags: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "strength": round(self.strength, 3),
            "room": self.room,
            "tags": self.tags[:8],
            "links": self.links[:6],
        }


@dataclass
class ProceduralSkill:
    choice_key: str
    room: str
    executions: int = 0
    success: float = 0.5
    motor_channels: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "choice_key": self.choice_key,
            "room": self.room,
            "executions": self.executions,
            "success": round(self.success, 3),
            "motor_channels": self.motor_channels[:8],
        }


@dataclass
class TypedMemorySystems:
    semantic: dict[str, SemanticConcept] = field(default_factory=dict)
    procedural: dict[str, ProceduralSkill] = field(default_factory=dict)
    emotional_tags: list[str] = field(default_factory=list)
    _path_sem: Path | None = field(default=None, init=False)
    _path_proc: Path | None = field(default=None, init=False)

    def bind_state_dir(self, state_dir: Path) -> None:
        base = Path(state_dir)
        self._path_sem = base / "semantic_memory.json"
        self._path_proc = base / "procedural_memory.json"
        self.load()

    def load(self) -> None:
        if self._path_sem and self._path_sem.is_file():
            raw = json.loads(self._path_sem.read_text(encoding="utf-8"))
            for item in raw.get("concepts") or []:
                c = SemanticConcept(
                    key=str(item["key"]),
                    label=str(item.get("label", item["key"])),
                    strength=float(item.get("strength", 0.5)),
                    room=str(item.get("room", "")),
                    tags=list(item.get("tags") or []),
                    links=list(item.get("links") or []),
                )
                self.semantic[c.key] = c
        if self._path_proc and self._path_proc.is_file():
            raw = json.loads(self._path_proc.read_text(encoding="utf-8"))
            for item in raw.get("skills") or []:
                k = f"{item['choice_key']}@{item.get('room', '')}"
                self.procedural[k] = ProceduralSkill(
                    choice_key=str(item["choice_key"]),
                    room=str(item.get("room", "")),
                    executions=int(item.get("executions", 0)),
                    success=float(item.get("success", 0.5)),
                    motor_channels=[int(x) for x in item.get("motor_channels") or []],
                )

    def save(self) -> None:
        if self._path_sem:
            self._path_sem.parent.mkdir(parents=True, exist_ok=True)
            self._path_sem.write_text(
                json.dumps(
                    {"concepts": [c.to_dict() for c in self.semantic.values()]},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        if self._path_proc:
            self._path_proc.parent.mkdir(parents=True, exist_ok=True)
            self._path_proc.write_text(
                json.dumps(
                    {"skills": [s.to_dict() for s in self.procedural.values()]},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

    def classify_episode(self, *, label: str, tags: list[str], modality: str, motor: list[int]) -> str:
        tset = {t.lower() for t in tags}
        if "curriculum" in tset or "brain_facts" in tset or modality == "document":
            return "semantic"
        if "world" in tset and motor and ("explore" in tset or "intention" in tset):
            return "procedural"
        if "world" in tset or "vision" in tset or "social" in tset:
            return "episodic"
        return "episodic"

    def after_episode(
        self,
        brain: InfantApeBrain,
        *,
        label: str,
        tags: list[str],
        modality: str,
        motor: list[int],
        room: str,
        valence: float,
        remembered: bool,
    ) -> dict[str, Any]:
        kind = self.classify_episode(label=label, tags=tags, modality=modality, motor=motor)
        out: dict[str, Any] = {"memory_type": kind}

        if kind == "semantic":
            key = label.split("@")[0].strip()[:48] or "concepto"
            c = self.semantic.get(key)
            if c:
                c.strength = float(np.clip(c.strength + 0.08, 0, 1))
                c.tags = list(set(c.tags + tags[:4]))[:12]
            else:
                self.semantic[key] = SemanticConcept(
                    key=key, label=label[:60], strength=0.45, room=room, tags=tags[:6]
                )
            out["semantic_key"] = key

        elif kind == "procedural":
            ck = brain.deliberation.last.choice_key or tags[-1] if tags else "explore"
            sk_key = f"{ck}@{room}"
            sk = self.procedural.get(sk_key)
            channels = motor[:6] or MOTOR_AFFINITY.get(ck, [])[:6]
            if sk:
                sk.executions += 1
                sk.success = float(np.clip(0.85 * sk.success + 0.15 * (0.6 if motor else 0.4), 0, 1))
                sk.motor_channels = list(set(sk.motor_channels + channels))[:10]
            else:
                self.procedural[sk_key] = ProceduralSkill(
                    choice_key=ck, room=room, executions=1, motor_channels=channels
                )
            self._sync_procedural_to_basal_ganglia(brain, ck, channels)
            out["skill_key"] = sk_key

        if abs(valence) > 0.35:
            self.emotional_tags.append(label[:40])
            self.emotional_tags = self.emotional_tags[-24:]

        return out

    def _sync_procedural_to_basal_ganglia(
        self, brain: InfantApeBrain, choice_key: str, channels: list[int]
    ) -> None:
        bg = brain.basal_ganglia
        bump = 0.04 * (0.5 + brain.modulators.dopamine)
        for idx in channels or MOTOR_AFFINITY.get(choice_key, []):
            if 0 <= idx < bg.habit.size:
                bg.habit[idx] = float(np.clip(bg.habit[idx] + bump, 0, 3.0))

    def procedural_motor_bias(self, brain: InfantApeBrain, choice_key: str, room: str) -> np.ndarray:
        n = brain.cortex.n_motor
        bias = np.zeros(n, dtype=np.float32)
        sk = self.procedural.get(f"{choice_key}@{room}")
        if not sk or sk.executions < 2:
            return bias
        weight = float(np.clip(0.15 + sk.success * 0.35, 0.1, 0.55))
        for idx in sk.motor_channels:
            if 0 <= idx < n:
                bias[idx] += weight
        for idx in MOTOR_AFFINITY.get(choice_key, []):
            if 0 <= idx < n:
                bias[idx] += weight * 0.4
        return bias

    def semantic_context_bias(self, brain: InfantApeBrain, room: str) -> np.ndarray:
        n = brain.n_sensory
        bias = np.zeros(n, dtype=np.float32)
        relevant = [c for c in self.semantic.values() if not c.room or c.room == room]
        relevant.sort(key=lambda c: c.strength, reverse=True)
        for i, c in enumerate(relevant[:4]):
            seed = hash(c.key) & 0xFFFF
            rng = np.random.default_rng(seed)
            bump = rng.normal(0, 0.06, size=min(n, 32)).astype(np.float32)
            bias[: bump.size] += bump * c.strength * 0.15
        return bias

    def consolidate_semantic_from_episode(self, brain: InfantApeBrain, mem: dict) -> None:
        label = str(mem.get("label", ""))[:60]
        if not label:
            return
        key = label.split("@")[0].strip()[:48]
        room = str(mem.get("room", ""))
        c = self.semantic.get(key)
        tags = mem.get("tags") or []
        boost = 0.18 if "conscious" in tags else 0.12
        if c:
            c.strength = float(np.clip(c.strength + boost, 0, 1))
        else:
            self.semantic[key] = SemanticConcept(
                key=key, label=label, strength=0.58 if "conscious" in tags else 0.55, room=room
            )

    def tag_emotional_memory(self, mem: dict) -> None:
        lbl = str(mem.get("label", ""))[:40]
        if lbl:
            self.emotional_tags.append(lbl)
            self.emotional_tags = self.emotional_tags[-24:]

    def to_dict(self) -> dict[str, Any]:
        top_sem = sorted(self.semantic.values(), key=lambda c: c.strength, reverse=True)[:6]
        top_proc = sorted(self.procedural.values(), key=lambda s: s.executions, reverse=True)[:6]
        return {
            "semantic_count": len(self.semantic),
            "procedural_count": len(self.procedural),
            "emotional_tags": self.emotional_tags[-6:],
            "top_concepts": [c.to_dict() for c in top_sem],
            "top_skills": [s.to_dict() for s in top_proc],
        }
