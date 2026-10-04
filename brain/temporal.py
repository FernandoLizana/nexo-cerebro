"""
Percepción temporal — Nexo siente pasar el tiempo (ritmo circadiano, duración, cambios de fase).

Codifica el tiempo en vectores sensoriales para hipocampo y corteza.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .environment import PHASE_LABELS_ES


@dataclass
class TemporalPerception:
    last_phase: str = ""
    last_total_minute: int = -1
    last_observe: dict = field(default_factory=dict)
    ticks_at_phase: int = 0

    def observe(self, ambient: dict, *, ticks: int = 1) -> dict[str, Any]:
        hour = int(ambient.get("hour", 12))
        minute = int(ambient.get("minute", 0))
        phase = ambient.get("phase", "day")
        total_min = hour * 60 + minute
        phase_changed = bool(self.last_phase and phase != self.last_phase)
        minute_delta = 0
        if self.last_total_minute >= 0 and not ambient.get("realtime", True):
            minute_delta = (total_min - self.last_total_minute) % 1440
        elif self.last_total_minute >= 0:
            minute_delta = max(0, total_min - self.last_total_minute)

        if phase == self.last_phase:
            self.ticks_at_phase += ticks
        else:
            self.ticks_at_phase = ticks

        felt = self._felt_sensation(hour, minute, phase, phase_changed, minute_delta, ambient)
        passage = self._passage_label(minute_delta, phase_changed, ambient)

        state = {
            "clock": ambient.get("clock", "??:??"),
            "hour": hour,
            "minute": minute,
            "phase": phase,
            "phase_label": PHASE_LABELS_ES.get(phase, phase),
            "season": ambient.get("season", ""),
            "weekday": ambient.get("weekday", ""),
            "time_of_day": ambient.get("time_of_day", 0.5),
            "light_level": ambient.get("light_level", 1.0),
            "realtime": ambient.get("realtime", True),
            "paused": ambient.get("paused", False),
            "time_scale": ambient.get("time_scale", 1.0),
            "phase_changed": phase_changed,
            "minute_delta": minute_delta,
            "felt": felt,
            "passage": passage,
            "ticks_at_phase": self.ticks_at_phase,
            "is_morning": 5 <= hour < 11,
            "is_afternoon": 12 <= hour < 18,
            "is_evening": 18 <= hour < 22,
            "is_night": phase == "night" or hour >= 22 or hour < 5,
        }
        self.last_phase = phase
        self.last_total_minute = total_min
        self.last_observe = state
        return state

    def _felt_sensation(
        self,
        hour: int,
        minute: int,
        phase: str,
        phase_changed: bool,
        minute_delta: int,
        ambient: dict,
    ) -> str:
        if ambient.get("paused"):
            return "el tiempo está detenido"
        if phase_changed:
            return f"cambió a {PHASE_LABELS_ES.get(phase, phase)}"
        if phase == "dawn" or (5 <= hour < 7):
            return "amanecer — luz que crece"
        if 7 <= hour < 11:
            return "mañana — día recién empezado"
        if 11 <= hour < 14:
            return "mediodía — sol alto"
        if 14 <= hour < 18:
            return "tarde que avanza"
        if phase == "dusk" or 18 <= hour < 22:
            return "atardecer — luz que se apaga"
        if hour >= 22 or hour < 5:
            return "noche profunda"
        if minute_delta > 20 and not ambient.get("realtime", True):
            return f"pasaron ~{minute_delta} minutos"
        return f"sense las {hour:02d}:{minute:02d}"

    def _passage_label(self, minute_delta: int, phase_changed: bool, ambient: dict) -> str:
        if ambient.get("paused"):
            return "pausa"
        if phase_changed:
            return "transición de fase"
        if minute_delta > 45:
            return "rato largo"
        if minute_delta > 12:
            return "un rato"
        if minute_delta > 0:
            return "instante"
        return "ahora"

    def encode(self, n: int, ambient: dict) -> np.ndarray:
        """Huella circadiana sin/cos + fase para tálamo."""
        vec = np.zeros(n, dtype=np.float32)
        if n <= 0:
            return vec
        tod = float(ambient.get("time_of_day", 0.5))
        ang = 2 * np.pi * tod
        vec[0] = 0.5 + 0.5 * np.sin(ang)
        if n > 1:
            vec[1] = 0.5 + 0.5 * np.cos(ang)
        phase_map = {"dawn": 0.25, "day": 0.55, "dusk": 0.75, "night": 0.12}
        if n > 2:
            vec[2] = phase_map.get(ambient.get("phase", "day"), 0.5)
        if n > 3:
            vec[3] = float(ambient.get("light_level", 0.5))
        season_map = {"primavera": 0.2, "verano": 0.85, "otoño": 0.55, "invierno": 0.1}
        if n > 4:
            vec[4] = season_map.get(ambient.get("season", ""), 0.4)
        hour = int(ambient.get("hour", 12))
        if n > 5:
            vec[5] = hour / 24.0
        return vec

    def percepts(self, state: dict | None = None) -> list[dict]:
        s = state or self.last_observe
        if not s:
            return []
        out = [
            {
                "label": s.get("felt", "tiempo"),
                "modality": "temporal",
                "salience": 0.42 if not s.get("phase_changed") else 0.62,
                "kind": "time",
                "valence": 0.05,
            },
            {
                "label": f"{s.get('phase_label', 'día')} · {s.get('clock', '')}",
                "modality": "temporal",
                "salience": 0.38,
                "kind": "circadian",
                "valence": 0.0,
            },
        ]
        if s.get("phase_changed"):
            out.insert(
                0,
                {
                    "label": f"transición — {s.get('passage', '')}",
                    "modality": "temporal",
                    "salience": 0.72,
                    "kind": "time_shift",
                    "valence": 0.1,
                },
            )
        if s.get("is_night"):
            out.append(
                {
                    "label": "ritmo nocturno",
                    "modality": "temporal",
                    "salience": 0.35,
                    "kind": "night",
                    "valence": -0.05,
                }
            )
        return out

    def to_dict(self) -> dict:
        return dict(self.last_observe) if self.last_observe else {}
