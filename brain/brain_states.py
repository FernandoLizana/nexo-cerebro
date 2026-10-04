"""
Estados cerebrales — vigilia, somnolencia, sueño (Brain Facts Ch.9 Brain States).

Modula apertura talámica y ganancia cortical según presión de sueño y ritmo circadiano.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass
class BrainStateController:
    state: str = "awake"
    thalamic_gate: float = 0.72
    cortical_gain: float = 1.0
    rem_tendency: float = 0.0

    def integrate(self, brain: InfantApeBrain, ambient: dict | None = None) -> dict[str, Any]:
        env = ambient or {}
        sleep_p = brain.brainstem.sleep_pressure
        hour = int(env.get("hour", 12))
        light = float(env.get("light_level", 1.0))
        ach = brain.modulators.acetylcholine
        is_night = env.get("phase") == "night" or hour >= 22 or hour < 6

        if sleep_p > 0.82:
            self.state = "deep_sleep"
            self.thalamic_gate = 0.18
            self.cortical_gain = 0.55
        elif sleep_p > 0.55:
            self.state = "drowsy" if not is_night else "nrem"
            self.thalamic_gate = 0.42
            self.cortical_gain = 0.72
        elif is_night and sleep_p > 0.35:
            self.state = "nrem"
            self.thalamic_gate = 0.55
            self.cortical_gain = 0.85
        else:
            self.state = "awake"
            self.thalamic_gate = float(np.clip(0.55 + ach * 0.35 + light * 0.15, 0.35, 0.95))
            self.cortical_gain = float(np.clip(0.85 + ach * 0.2, 0.7, 1.15))

        self.rem_tendency = float(np.clip(sleep_p * 0.6 + (0.2 if is_night else 0), 0, 1))

        brain.thalamus.arousal_gate = self.thalamic_gate
        brain.cortex.synaptic_gain = float(
            np.clip(brain.profile.synaptic_gain * self.cortical_gain, brain.profile.synaptic_gain * 0.5, brain.profile.synaptic_gain * 1.25)
        )

        return {
            "state": self.state,
            "thalamic_gate": round(self.thalamic_gate, 3),
            "cortical_gain": round(self.cortical_gain, 3),
            "rem_tendency": round(self.rem_tendency, 3),
        }
