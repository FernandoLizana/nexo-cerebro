"""
Lecho vascular cerebral simplificado — glucosa, oxígeno, integridad BBB.

Modula ganancia sináptica según metabolismo; no elige acciones.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class CerebralVascularBed:
    glucose: float = 0.88
    oxygen: float = 0.92
    bbb_integrity: float = 0.94
    cerebral_blood_flow: float = 0.75
    lactate: float = 0.08

    _base_gain: float = field(default=0.0, init=False)

    def step(self, brain) -> dict[str, float]:
        body = brain.body
        activity = float(
            np.mean(
                [
                    float(brain.cortex.associative.spikes.mean()),
                    float(brain.cortex.prefrontal.spikes.mean()),
                ]
            )
        )
        hunger = float(getattr(body, "hunger", 0.0) or 0.0)
        fatigue = float(getattr(body, "fatigue", 0.0) or 0.0)
        pain = float(body.total_pain() if hasattr(body, "total_pain") else 0.0)
        sleep_p = float(brain.brainstem.sleep_pressure)

        metabolic_demand = activity * 0.12 + pain * 0.08
        self.glucose = float(
            np.clip(
                self.glucose * 0.992
                + (1.0 - hunger) * 0.018
                - metabolic_demand * 0.04
                + (0.02 if sleep_p > 0.6 else 0.0),
                0.15,
                1.0,
            )
        )
        self.oxygen = float(
            np.clip(
                self.oxygen * 0.994
                + self.cerebral_blood_flow * 0.012
                - metabolic_demand * 0.05
                - fatigue * 0.02,
                0.2,
                1.0,
            )
        )
        self.cerebral_blood_flow = float(
            np.clip(0.55 + activity * 0.35 + (1 - sleep_p) * 0.15 - pain * 0.1, 0.25, 1.0)
        )
        stress = float(brain.hypothalamus.cortisol)
        self.bbb_integrity = float(
            np.clip(self.bbb_integrity * 0.998 - stress * 0.004 - lactate_penalty(self.lactate), 0.5, 1.0)
        )
        self.lactate = float(np.clip(self.lactate * 0.95 + metabolic_demand * 0.08, 0, 0.45))

        if self._base_gain <= 0:
            self._base_gain = float(brain.profile.synaptic_gain)
        perfusion = 0.35 * self.glucose + 0.45 * self.oxygen + 0.2 * self.cerebral_blood_flow
        bbb_factor = 0.85 + 0.15 * self.bbb_integrity
        target_gain = self._base_gain * (0.82 + 0.22 * perfusion) * bbb_factor
        brain.cortex.synaptic_gain = float(
            np.clip(target_gain, self._base_gain * 0.72, self._base_gain * 1.12)
        )
        return self.to_dict()

    def to_dict(self) -> dict[str, Any]:
        return {
            "glucose": round(self.glucose, 3),
            "oxygen": round(self.oxygen, 3),
            "bbb_integrity": round(self.bbb_integrity, 3),
            "cerebral_blood_flow": round(self.cerebral_blood_flow, 3),
            "lactate": round(self.lactate, 3),
        }


def lactate_penalty(lactate: float) -> float:
    return max(0.0, float(lactate) - 0.2) * 0.15
