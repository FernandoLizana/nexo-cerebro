"""
Vestibular — equilibrio, aceleración y vértigo desde biomecánica.

Modula arousal y nocicepción leve; no motor directo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class VestibularPathway:
    equilibrium: float = 1.0
    vertigo: float = 0.0
    linear_accel: float = 0.0
    angular_accel: float = 0.0
    fall_risk: float = 0.0

    def integrate(self, brain) -> tuple[np.ndarray, dict[str, Any]]:
        bm = brain.biomech
        speed = float(np.hypot(bm.vx, bm.vy))
        self.equilibrium = float(np.clip(bm.equilibrium, 0, 1))
        self.linear_accel = float(np.clip(np.hypot(bm.ax, bm.ay) / 12.0, 0, 1))
        self.angular_accel = float(np.clip(abs(bm.angular_velocity) / 4.0, 0, 1))
        self.vertigo = float(
            np.clip(
                (1.0 - self.equilibrium) * 0.6
                + self.angular_accel * 0.35
                + (0.25 if bm.ragdoll_active else 0.0),
                0,
                1,
            )
        )
        self.fall_risk = float(
            np.clip(
                (1.0 - self.equilibrium) * 0.5
                + self.vertigo * 0.3
                + (0.2 if not bm.on_ground else 0.0),
                0,
                1,
            )
        )

        n = max(6, brain.n_sensory // 20)
        vec = np.array(
            [
                self.equilibrium,
                1.0 - self.vertigo,
                self.linear_accel,
                self.angular_accel,
                min(1.0, speed / 14.0),
                self.fall_risk,
            ],
            dtype=np.float32,
        )
        if vec.size < n:
            vec = np.pad(vec, (0, n - vec.size))
        vec = vec[:n]
        m = float(vec.max())
        if m > 1e-6:
            vec = vec / m

        meta = {
            "equilibrium": round(self.equilibrium, 3),
            "vertigo": round(self.vertigo, 3),
            "fall_risk": round(self.fall_risk, 3),
            "ragdoll": bm.ragdoll_active,
        }
        return vec, meta

    def to_dict(self) -> dict[str, Any]:
        return {
            "equilibrium": round(self.equilibrium, 3),
            "vertigo": round(self.vertigo, 3),
            "linear_accel": round(self.linear_accel, 3),
            "angular_accel": round(self.angular_accel, 3),
            "fall_risk": round(self.fall_risk, 3),
        }
