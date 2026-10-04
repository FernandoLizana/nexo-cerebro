"""
Predicción temporal de necesidades — cuándo vendrá hambre/sed/descanso.

Sesga memoria de trabajo y drives suavemente; no escribe choice_key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class TemporalPredictor:
    """Interval timing simplificado desde ritmo circadiano + historial de comidas."""

    default_meal_hours: tuple[int, ...] = (8, 13, 20)
    last_food_tick: int = 0
    last_water_tick: int = 0
    predictions: dict[str, Any] = field(default_factory=dict)

    def _minutes_to_next_meal(self, hour: int, minute: int) -> int:
        now = hour * 60 + minute
        best = 1440
        for mh in self.default_meal_hours:
            target = mh * 60
            delta = (target - now) % 1440
            if delta < best:
                best = delta
        return int(best)

    def update(self, brain) -> dict[str, Any]:
        ambient = brain.world.ambient()
        hour = int(ambient.get("hour", 12))
        minute = int(ambient.get("minute", 0))
        tick = int(brain.lifecycle.age_ticks)

        food_eta = self._minutes_to_next_meal(hour, minute)
        thirst_eta = max(30, 180 - (tick - self.last_water_tick) * 7)
        sleep_circ = (brain._last_env or {}).get("circadian") or {}
        sleep_eta = int(max(20, (1.0 - float(sleep_circ.get("alertness", 0.5))) * 240))

        hunger = float(brain.body.hunger if hasattr(brain.body, "hunger") else 0)
        thirst = float(brain.body.thirst if hasattr(brain.body, "thirst") else 0)
        food_conf = float(np.clip(0.35 + (1.0 - hunger) * 0.4 + (1.0 if food_eta < 90 else 0.0) * 0.2, 0.2, 0.9))
        water_conf = float(np.clip(0.3 + thirst * 0.5 + (1.0 if thirst_eta < 120 else 0.0) * 0.15, 0.2, 0.85))

        self.predictions = {
            "seek_food_eta_min": food_eta,
            "seek_water_eta_min": int(thirst_eta),
            "sleep_eta_min": sleep_eta,
            "food_confidence": round(food_conf, 3),
            "water_confidence": round(water_conf, 3),
            "next_meal_hour": min(
                self.default_meal_hours,
                key=lambda mh: (mh * 60 - (hour * 60 + minute)) % 1440,
            ),
        }
        return dict(self.predictions)

    def note_event(self, brain, event_type: str) -> None:
        tick = int(brain.lifecycle.age_ticks)
        if event_type in ("eat", "food", "seek_food"):
            self.last_food_tick = tick
        if event_type in ("drink", "water", "seek_water"):
            self.last_water_tick = tick

    def apply_drive_bias(self, drives: dict[str, float]) -> None:
        """Sesgo suave cuando la predicción es inminente (<45 min)."""
        p = self.predictions
        if not p:
            return
        if int(p.get("seek_food_eta_min", 999)) < 45:
            conf = float(p.get("food_confidence", 0.3))
            drives["seek_food"] = float(np.clip(drives.get("seek_food", 0) + 0.08 * conf, 0, 1))
        if int(p.get("seek_water_eta_min", 999)) < 40:
            conf = float(p.get("water_confidence", 0.3))
            drives["seek_water"] = float(np.clip(drives.get("seek_water", 0) + 0.07 * conf, 0, 1))
        if int(p.get("sleep_eta_min", 999)) < 50:
            drives["sleep_need"] = float(np.clip(drives.get("sleep_need", 0) + 0.06, 0, 1))

    def prime_working_memory(self, brain) -> None:
        p = self.predictions
        if not p or not brain.experiment_flags.enable_temporal_prediction:
            return
        if int(p.get("seek_food_eta_min", 999)) < 60:
            brain.working_memory.push(
                label=f"predicción: comida en ~{p['seek_food_eta_min']} min",
                modality="prediction",
                room=brain.world.current_room(),
                tags=["temporal", "food"],
                valence=0.05,
            )

    def to_dict(self) -> dict[str, Any]:
        return dict(self.predictions)
