"""
Lenguaje grounded: palabras ↔ objetos/drives del mundo 2D.

Libre albedrío:
  - Grounding **nunca** asigna ``choice_key`` ni llama a ``apply_motor``.
  - Solo (1) refuerza drives, (2) inyecta patrón sensorial, (3) anota meta en WM.
  - La deliberación PFC sigue eligiendo la acción.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .encode import encode_text

# kind = furniture/world target; drive = homeostatic channel (not action key)
GROUNDING_LEXICON: tuple[dict[str, Any], ...] = (
    {
        "id": "fridge",
        "kind": "fridge",
        "drive": "seek_food",
        "label": "nevera",
        "words": ("nevera", "fridge", "comida", "comer", "hambre", "alimento", "refrigerador"),
    },
    {
        "id": "desk",
        "kind": "desk",
        "drive": "seek_curiosity",
        "label": "escritorio",
        "words": ("escritorio", "desk", "estudiar", "libro", "leer", "aprender", "investigación"),
    },
    {
        "id": "bed",
        "kind": "bed",
        "drive": "seek_rest",
        "label": "cama",
        "words": ("cama", "bed", "descansar", "dormir", "sueño", "acostar"),
    },
    {
        "id": "tv",
        "kind": "tv",
        "drive": "seek_stimulus",
        "label": "televisión",
        "words": ("tele", "tv", "televisión", "pantalla", "ver"),
    },
    {
        "id": "bath",
        "kind": "bath",
        "drive": "seek_hygiene",
        "label": "bañera",
        "words": ("bañera", "bath", "baño", "higiene", "lavar", "ducha"),
    },
    {
        "id": "toilet",
        "kind": "toilet",
        "drive": "seek_bathroom",
        "label": "inodoro",
        "words": ("inodoro", "toilet", "wc", "baño", "orinar"),
    },
    {
        "id": "stove",
        "kind": "stove",
        "drive": "seek_cook",
        "label": "cocina",
        "words": ("estufa", "stove", "cocinar", "fogón", "hornilla"),
    },
    {
        "id": "companion",
        "kind": "companion",
        "drive": "seek_companion",
        "label": "Nira",
        "words": ("nira", "compañera", "amiga", "ella", "junto"),
    },
    {
        "id": "garden",
        "kind": "garden",
        "drive": "seek_food",
        "label": "jardín",
        "words": ("jardín", "garden", "cosechar", "planta", "fruta"),
    },
)


@dataclass
class GroundingHit:
    concept_id: str
    kind: str
    drive: str
    label: str
    strength: float
    matched_word: str = ""


@dataclass
class GroundingState:
    """Sesgo pendiente tras oír al cuidador; decae cada tick."""

    hits: list[GroundingHit] = field(default_factory=list)
    drive_boost: dict[str, float] = field(default_factory=dict)
    sensory_trace: np.ndarray | None = None
    last_text: str = ""
    ticks_left: int = 0
    applications: int = 0

    def clear(self) -> None:
        self.hits.clear()
        self.drive_boost.clear()
        self.sensory_trace = None
        self.last_text = ""
        self.ticks_left = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_text": self.last_text[:80],
            "ticks_left": self.ticks_left,
            "hits": [
                {
                    "id": h.concept_id,
                    "kind": h.kind,
                    "drive": h.drive,
                    "label": h.label,
                    "strength": round(h.strength, 3),
                    "word": h.matched_word,
                }
                for h in self.hits[:6]
            ],
            "drive_boost": {k: round(v, 3) for k, v in self.drive_boost.items()},
            "applications": self.applications,
            "agency_note": "Grounding biases drives/sensory only; deliberation selects actions",
        }


def parse_grounding(text: str) -> list[GroundingHit]:
    low = (text or "").lower()
    if not low.strip():
        return []
    hits: list[GroundingHit] = []
    for concept in GROUNDING_LEXICON:
        best_w = ""
        best_s = 0.0
        for w in concept["words"]:
            if w in low:
                # palabras más específicas → más fuerza
                s = 0.45 + 0.08 * min(len(w), 8)
                if s > best_s:
                    best_s = s
                    best_w = w
        if best_s > 0:
            hits.append(
                GroundingHit(
                    concept_id=str(concept["id"]),
                    kind=str(concept["kind"]),
                    drive=str(concept["drive"]),
                    label=str(concept["label"]),
                    strength=float(min(0.95, best_s)),
                    matched_word=best_w,
                )
            )
    hits.sort(key=lambda h: -h.strength)
    return hits


def apply_utterance_grounding(
    brain,
    text: str,
    *,
    duration_ticks: int = 8,
    sensory_gain: float = 0.22,
) -> GroundingState:
    """
    Registra grounding desde texto del cuidador.
    No selecciona motor / choice_key.
    """
    state: GroundingState = getattr(brain, "grounding", None) or GroundingState()
    hits = parse_grounding(text)
    state.hits = hits
    state.last_text = (text or "")[:120]
    state.ticks_left = max(0, int(duration_ticks)) if hits else 0
    state.drive_boost = {}
    for h in hits:
        state.drive_boost[h.drive] = float(
            min(0.55, state.drive_boost.get(h.drive, 0.0) + 0.28 * h.strength)
        )

    n = int(getattr(brain, "n_sensory", 128))
    if hits:
        blend = np.zeros(n, dtype=np.float32)
        for h in hits[:3]:
            enc = encode_text(f"ground:{h.kind}:{h.label}:{h.matched_word}", n)
            blend = np.clip(blend + enc * (sensory_gain * h.strength), 0, 1)
        state.sensory_trace = blend
        if hasattr(brain, "working_memory"):
            top = hits[0]
            brain.working_memory.push(
                label=f"oír: {top.label}",
                modality="language",
                room=brain.world.current_room() if hasattr(brain, "world") else "",
                valence=0.1,
                goal=f"atender {top.label}",
                tags=["grounding", top.kind, top.drive],
                salience=float(top.strength),
            )
    else:
        state.sensory_trace = None

    brain.grounding = state
    state.applications += 1
    return state


def merge_grounding_drives(drives: dict[str, float], state: GroundingState | None) -> dict[str, float]:
    if not state or state.ticks_left <= 0 or not state.drive_boost:
        return drives
    out = dict(drives)
    fade = state.ticks_left / max(state.ticks_left + 1, 8)
    for k, v in state.drive_boost.items():
        out[k] = float(min(1.0, out.get(k, 0.0) + v * fade))
    return out


def merge_grounding_sensory(
    sensory: np.ndarray,
    state: GroundingState | None,
    *,
    gain: float = 0.35,
) -> np.ndarray:
    if not state or state.ticks_left <= 0 or state.sensory_trace is None:
        return sensory
    base = np.asarray(sensory, dtype=np.float32).ravel()
    tr = np.asarray(state.sensory_trace, dtype=np.float32).ravel()
    n = min(base.size, tr.size)
    if n <= 0:
        return sensory
    fade = state.ticks_left / max(state.ticks_left + 2, 8)
    out = base.copy()
    out[:n] = np.clip(out[:n] * (1.0 - gain * fade) + tr[:n] * (gain * fade), 0, 1)
    return out


def tick_grounding(state: GroundingState | None) -> None:
    if not state:
        return
    if state.ticks_left > 0:
        state.ticks_left -= 1
    if state.ticks_left <= 0:
        state.drive_boost.clear()
        state.sensory_trace = None
