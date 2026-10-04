"""
Sistemas de neuromodulación (aprox. núcleos reales).

VTA → dopamina (recompensa, plasticidad)
Raphe → serotonina (ánimo, impulsividad)
Locus coeruleus → noradrenalina (alerta)
Basal forebrain → acetilcolina (atención, codificación)
Corteza → GABA / glutamato (inhibición / excitación locales)
"""

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
    oxytocin: float = 0.42

    history: list[dict] = field(default_factory=list)

    def update(
        self,
        *,
        reward: float,
        stress: float,
        novelty: float,
        attention: float,
        sleep_pressure: float,
        social_bond: float = 0.0,
    ) -> dict:
        self.dopamine = float(
            np.clip(0.65 * self.dopamine + 0.35 * (0.3 + reward * 0.55 + novelty * 0.25), 0, 1)
        )
        self.serotonin = float(
            np.clip(0.7 * self.serotonin + 0.3 * (0.55 - stress * 0.35 + reward * 0.15), 0, 1)
        )
        self.norepinephrine = float(
            np.clip(
                0.6 * self.norepinephrine
                + 0.4 * (0.25 + stress * 0.45 + attention * 0.35 - sleep_pressure * 0.4),
                0,
                1,
            )
        )
        self.acetylcholine = float(
            np.clip(0.68 * self.acetylcholine + 0.32 * (0.25 + attention * 0.5 + novelty * 0.35), 0, 1)
        )
        self.gaba_tone = float(np.clip(0.72 * self.gaba_tone + 0.28 * (0.35 + stress * 0.25), 0, 1))
        self.glutamate_drive = float(
            np.clip(0.7 * self.glutamate_drive + 0.3 * (0.4 + attention * 0.35 + reward * 0.2), 0, 1)
        )
        self.oxytocin = float(
            np.clip(0.78 * self.oxytocin + 0.22 * (0.25 + social_bond * 0.55 + max(reward, 0) * 0.2), 0, 1)
        )
        snap = self.to_dict()
        self.history.append(snap)
        if len(self.history) > 30:
            self.history.pop(0)
        return snap

    def gain_scale(self) -> float:
        return 0.75 + 0.35 * self.glutamate_drive + 0.2 * self.norepinephrine

    def plasticity_scale(self) -> float:
        return 0.5 + 0.9 * self.dopamine + 0.45 * self.acetylcholine

    def inhibition_scale(self) -> float:
        return 0.35 + 0.85 * self.gaba_tone + 0.15 * self.serotonin

    def nmda_open_probability(self, v_mean: float) -> float:
        """Compuerta tipo NMDA (dependiente de voltaje)."""
        return float(1.0 / (1.0 + np.exp(-(v_mean + 50.0) / 12.0)))

    def to_dict(self) -> dict:
        return {
            "dopamine": round(self.dopamine, 3),
            "serotonin": round(self.serotonin, 3),
            "norepinephrine": round(self.norepinephrine, 3),
            "acetylcholine": round(self.acetylcholine, 3),
            "gaba_tone": round(self.gaba_tone, 3),
            "glutamate_drive": round(self.glutamate_drive, 3),
            "oxytocin": round(self.oxytocin, 3),
        }
