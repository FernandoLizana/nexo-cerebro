"""
Núcleo supraquiasmático (SCN) simplificado — reloj interno vs luz ambiental.

Modela jet lag: el reloj interno se desplaza lentamente hacia la luz.
No elige acciones — sesga circadian_profile y cortisol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .environment import circadian_profile, phase_from_hour


@dataclass
class SCNClock:
    """Reloj endógeno desacoplable del reloj solar (jet lag)."""

    phase_offset_min: float = 0.0
    sync_strength: float = 0.035
    last_light_min: int = field(default=-1, init=False)
    jet_lag_recovery: float = field(default=0.0, init=False)

    def light_minute(self, ambient: dict) -> int:
        hour = int(ambient.get("hour", 12))
        minute = int(ambient.get("minute", 0))
        return (hour * 60 + minute) % 1440

    def step(self, ambient: dict, *, dt_min: float = 7.0) -> dict[str, float]:
        light = self.light_minute(ambient)
        light_level = float(ambient.get("light_level", 0.5) or 0.5)
        if self.last_light_min < 0:
            self.last_light_min = light

        # Luz fuerte tira del reloj interno hacia la hora solar
        if light_level > 0.45:
            pull = self.sync_strength * light_level * float(dt_min)
            delta = ((light - self.last_light_min + 720) % 1440) - 720
            self.phase_offset_min = float(
                np.clip(self.phase_offset_min * (1 - pull) + delta * pull * 0.02, -360, 360)
            )

        # Recuperación lenta hacia cero (adaptación)
        self.phase_offset_min *= 0.9995
        self.jet_lag_recovery = float(1.0 - min(1.0, abs(self.phase_offset_min) / 180.0))
        self.last_light_min = light

        return {
            "phase_offset_min": round(self.phase_offset_min, 1),
            "jet_lag_recovery": round(self.jet_lag_recovery, 3),
            "scn_sync": round(0.5 + 0.5 * self.jet_lag_recovery, 3),
        }

    def shift_ambient(self, ambient: dict) -> dict:
        """Aplica offset interno a hora percibida (no muta reloj del mundo)."""
        out = dict(ambient)
        total = self.light_minute(ambient)
        shifted = int((total + self.phase_offset_min) % 1440)
        h, m = divmod(shifted, 60)
        out["scn_hour"] = h
        out["scn_minute"] = m
        out["scn_phase"] = phase_from_hour(h)
        out["jet_lag_min"] = round(self.phase_offset_min, 1)
        return out

    def circadian(self, ambient: dict) -> dict:
        shifted = self.shift_ambient(ambient)
        profile = circadian_profile(
            {
                **ambient,
                "hour": shifted["scn_hour"],
                "minute": shifted["scn_minute"],
                "phase": shifted["scn_phase"],
            }
        )
        profile["jet_lag_min"] = shifted.get("jet_lag_min", 0)
        profile["scn_sync"] = round(0.5 + 0.5 * self.jet_lag_recovery, 3)
        return profile

    def apply_jet_lag_shift(self, hours: float) -> None:
        """Perturbación manual (viaje / línea temporal brusca)."""
        self.phase_offset_min = float(np.clip(self.phase_offset_min + hours * 60.0, -720, 720))

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_offset_min": round(self.phase_offset_min, 1),
            "jet_lag_recovery": round(self.jet_lag_recovery, 3),
            "sync_strength": self.sync_strength,
        }
