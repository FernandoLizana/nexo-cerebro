"""Estado de neuromoduladores — port simplificado de legacy."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class NeuromodulatorState:
    dopamine: float = 0.52
    serotonin: float = 0.55
    norepinephrine: float = 0.45
    acetylcholine: float = 0.5
    gaba_tone: float = 0.4
    glutamate_drive: float = 0.55

    history: list[dict[str, float]] = field(default_factory=list)

    def update(
        self,
        *,
        reward: float,
        stress: float,
        novelty: float,
        attention: float,
        sleep_pressure: float,
    ) -> dict[str, float]:
        self.dopamine = float(
            np.clip(0.65 * self.dopamine + 0.35 * (0.3 + reward * 0.55 + novelty * 0.25), 0.0, 1.0)
        )
        self.serotonin = float(
            np.clip(0.7 * self.serotonin + 0.3 * (0.55 - stress * 0.35 + reward * 0.15), 0.0, 1.0)
        )
        self.norepinephrine = float(
            np.clip(
                0.6 * self.norepinephrine
                + 0.4 * (0.25 + stress * 0.45 + attention * 0.35 - sleep_pressure * 0.4),
                0.0,
                1.0,
            )
        )
        self.acetylcholine = float(
            np.clip(0.68 * self.acetylcholine + 0.32 * (0.25 + attention * 0.5 + novelty * 0.35), 0.0, 1.0)
        )
        self.gaba_tone = float(np.clip(0.72 * self.gaba_tone + 0.28 * (0.35 + stress * 0.25), 0.0, 1.0))
        self.glutamate_drive = float(
            np.clip(0.7 * self.glutamate_drive + 0.3 * (0.4 + attention * 0.35 + reward * 0.2), 0.0, 1.0)
        )
        snap = self.to_dict()
        self.history.append(snap)
        if len(self.history) > 30:
            self.history.pop(0)
        return snap

    def plasticity_scale(self) -> float:
        return 0.5 + 0.9 * self.dopamine + 0.45 * self.acetylcholine

    def to_dict(self) -> dict[str, float]:
        return {
            "dopamine": round(self.dopamine, 4),
            "serotonin": round(self.serotonin, 4),
            "norepinephrine": round(self.norepinephrine, 4),
            "acetylcholine": round(self.acetylcholine, 4),
            "gaba_tone": round(self.gaba_tone, 4),
            "glutamate_drive": round(self.glutamate_drive, 4),
        }
