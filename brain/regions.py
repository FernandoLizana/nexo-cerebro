"""
Regiones subcorticales simplificadas (aprox. anatomía → función).

Tálamo: relevo sensorial.
Amígdala: valencia / arousal.
Hipocampo: memoria episódica (patrones vividos).
Hipotálamo: estado homeostático y emocional → impulsa al personaje.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .memory_store import EpisodicMemoryStore


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na < 1e-6 or nb < 1e-6:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


@dataclass
class Thalamus:
    """Puerta sensorial: mezcla modalidades hacia la corteza."""

    n_out: int
    gains: dict[str, float] = field(
        default_factory=lambda: {
            "text": 1.0,
            "image": 1.1,
            "document": 0.95,
            "audio": 1.05,
            "world": 1.05,
            "time": 0.92,
            "occipital": 1.15,
            "temporal": 1.08,
            "parietal": 1.05,
            "frontal": 1.12,
        }
    )
    arousal_gate: float = 1.0

    def relay(self, modalities: dict[str, np.ndarray]) -> np.ndarray:
        out = np.zeros(self.n_out, dtype=np.float32)
        if not modalities:
            return out
        for name, vec in modalities.items():
            v = np.asarray(vec, dtype=np.float32).ravel()
            if v.size == 0:
                continue
            g = self.gains.get(name, 1.0)
            if v.size >= self.n_out:
                out += g * v[: self.n_out]
            else:
                out[: v.size] += g * v
        m = float(out.max()) if out.size else 0.0
        if m > 1e-6:
            out /= m
        return np.clip(out * self.arousal_gate, 0.0, 1.0)


@dataclass
class Amygdala:
    """Etiquetado emocional rápido a partir de rasgos del estímulo."""

    valence: float = 0.0
    arousal: float = 0.3

    def evaluate(
        self,
        pattern: np.ndarray,
        modality: str,
        *,
        gain: float = 1.0,
        social: bool = False,
    ) -> tuple[float, float]:
        p = np.asarray(pattern, dtype=np.float32)
        density = float(p.mean())
        entropy = float(-np.sum(p * np.log(p + 1e-6)) / max(p.size, 1))
        mod_bias = {
            "audio": 0.15,
            "image": 0.05,
            "document": -0.05,
            "text": 0.0,
            "social": 0.2,
            "world": 0.08,
            "video": 0.12,
        }.get(modality, 0.0)
        if social:
            mod_bias += 0.25
        valence = np.tanh((density * 2.2 - 0.9 + entropy * 0.25 + mod_bias) * gain)
        arousal = float(
            np.clip((0.25 + density * 0.55 + entropy * 0.35 + abs(mod_bias)) * gain, 0, 1)
        )
        self.valence = float(valence)
        self.arousal = arousal
        return self.valence, self.arousal


@dataclass
class Hippocampus:
    """Memoria episódica: patrón sensorial ↔ respuesta vivida (disco + caché RAM)."""

    capacity: int = 96
    store: EpisodicMemoryStore | None = None
    memories: list[dict] = field(default_factory=list)

    def _key(self, pattern: np.ndarray, label: str) -> str:
        h = hashlib.sha1(pattern.tobytes() + label.encode("utf-8")).hexdigest()[:12]
        return h

    def attach_store(self, store: EpisodicMemoryStore) -> None:
        self.store = store

    @property
    def size(self) -> int:
        if self.store:
            return self.store.total_count()
        return len(self.memories)

    def recall(
        self,
        pattern: np.ndarray,
        *,
        body: dict | None = None,
        room: str = "",
        motor: list[int] | None = None,
        semantic_text: str | None = None,
        brain=None,
    ) -> dict | None:
        if self.store:
            return self.store.recall(
                pattern,
                body=body,
                room=room,
                motor=motor,
                semantic_text=semantic_text,
                brain=brain,
            )
        if not self.memories:
            return None
        best, score = None, -1.0
        p = np.asarray(pattern, dtype=np.float32)
        for mem in self.memories:
            s = _cosine(p, mem["pattern"])
            if s > score:
                score, best = s, mem
        if best and score > 0.72:
            best["hits"] = best.get("hits", 0) + 1
            return {**best, "similarity": score}
        return None

    def consolidate(
        self,
        pattern: np.ndarray,
        *,
        label: str,
        modality: str,
        motor: list[int],
        valence: float,
        arousal: float,
        tags: list[str] | None = None,
        body: dict | None = None,
        room: str = "",
        olfaction: dict | None = None,
        affect: dict | None = None,
        posture: dict | None = None,
    ) -> dict:
        p = np.asarray(pattern, dtype=np.float32).copy()
        key = self._key(p, label)

        if self.store:
            return self.store.store(
                key,
                p,
                label=label,
                modality=modality,
                motor=motor,
                valence=valence,
                arousal=arousal,
                tags=tags,
                body=body,
                room=room,
                olfaction=olfaction,
                affect=affect,
                posture=posture,
            )

        for mem in self.memories:
            if mem["key"] == key:
                mem["count"] = mem.get("count", 1) + 1
                mem["motor"] = motor
                mem["valence"] = 0.7 * mem["valence"] + 0.3 * valence
                mem["arousal"] = 0.7 * mem["arousal"] + 0.3 * arousal
                if tags:
                    mem["tags"] = list(set(mem.get("tags", []) + tags))
                return mem
        entry = {
            "key": key,
            "label": label,
            "modality": modality,
            "pattern": p,
            "motor": motor,
            "valence": valence,
            "arousal": arousal,
            "count": 1,
            "hits": 0,
            "tags": tags or [],
        }
        self.memories.append(entry)
        if len(self.memories) > self.capacity:
            self.memories.pop(0)
        return entry

    def sample_for_replay(
        self,
        *,
        sleep_pressure: float = 0.0,
        modulators: Any | None = None,
        sleep_phase: str = "",
        replay_mode: str = "default",
    ) -> dict | None:
        if self.store:
            return self.store.sample_for_replay(
                sleep_pressure=sleep_pressure,
                modulators=modulators,
                sleep_phase=sleep_phase,
                replay_mode=replay_mode,
            )
        if not self.memories:
            return None
        return self.memories[np.random.randint(0, len(self.memories))]

    def list_recent(self, n: int = 8) -> list[dict]:
        if self.store:
            return self.store.list_recent(n)
        out = []
        for m in self.memories[-n:]:
            out.append(
                {
                    "label": m["label"],
                    "modality": m["modality"],
                    "count": m.get("count", 1),
                    "valence": round(m["valence"], 3),
                }
            )
        return out

    def clear(self) -> None:
        if self.store:
            self.store.clear()
        self.memories.clear()


@dataclass
class Hypothalamus:
    """
    Integración homeostática y neuroendocrina simplificada.

    Salidas modulan el personaje (ánimo, energía, apego al estímulo).
    """

    dopamine: float = 0.4
    cortisol: float = 0.2
    oxytocin: float = 0.3
    energy: float = 0.7
    familiarity: float = 0.0

    def update(
        self,
        *,
        valence: float,
        arousal: float,
        novelty: float,
        motor_activity: float,
        remembered: bool,
        hour: float | None = None,
        circadian: bool = False,
    ) -> dict:
        # Novedad → dopamina; estrés (arousal alto + valencia negativa) → cortisol
        self.dopamine = float(np.clip(0.6 * self.dopamine + 0.4 * (0.35 + novelty * 0.5 + max(valence, 0) * 0.3), 0, 1))
        stress = arousal * max(-valence, 0)
        self.cortisol = float(np.clip(0.7 * self.cortisol + 0.3 * stress, 0, 1))
        # Ritmo circadiano suave (pico matutino); no decide acciones.
        if circadian and hour is not None:
            h = float(hour) % 24.0
            # Pico ~08h, mínimo ~02h (aprox. cortisol humano)
            circ = 0.5 + 0.5 * np.cos((h - 8.0) * (2.0 * np.pi / 24.0))
            self.cortisol = float(np.clip(0.82 * self.cortisol + 0.18 * (0.15 + 0.55 * circ), 0, 1))
        self.oxytocin = float(
            np.clip(0.75 * self.oxytocin + 0.25 * (0.2 + max(valence, 0) * 0.4 + (0.15 if remembered else 0)), 0, 1)
        )
        self.energy = float(np.clip(self.energy - 0.02 * arousal + 0.01 * motor_activity, 0.15, 1))
        self.familiarity = float(np.clip(0.8 * self.familiarity + 0.2 * (1.0 if remembered else novelty), 0, 1))

        mood = self._mood_label(valence, arousal)
        return {
            "mood": mood,
            "dopamine": round(self.dopamine, 3),
            "cortisol": round(self.cortisol, 3),
            "oxytocin": round(self.oxytocin, 3),
            "energy": round(self.energy, 3),
            "familiarity": round(self.familiarity, 3),
        }

    @staticmethod
    def _mood_label(valence: float, arousal: float) -> str:
        if valence > 0.35 and arousal > 0.5:
            return "excited"
        if valence > 0.25:
            return "content"
        if valence < -0.25 and arousal > 0.45:
            return "stressed"
        if valence < -0.15:
            return "uneasy"
        if arousal > 0.55:
            return "curious"
        return "calm"
