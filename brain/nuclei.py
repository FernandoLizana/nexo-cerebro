"""
Núcleos del tronco y subcorticales que liberan neuromoduladores.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .neurotransmitters import NeuromodulatorState


@dataclass
class SubcorticalNuclei:
    """VTA, Raphe, LC, núcleo accumbens (recompensa)."""

    accumbens_activation: float = 0.3

    def step(
        self,
        mods: NeuromodulatorState,
        *,
        valence: float,
        arousal: float,
        novelty: float,
        motor_reward: float,
    ) -> dict:
        reward_signal = float(
            np.clip(0.4 * max(valence, 0) + 0.35 * novelty + 0.25 * motor_reward, 0, 1)
        )
        self.accumbens_activation = float(
            np.clip(0.7 * self.accumbens_activation + 0.3 * reward_signal, 0, 1)
        )
        stress = float(np.clip(arousal * max(-valence, 0), 0, 1))
        mods.update(
            reward=0.5 * reward_signal + 0.5 * self.accumbens_activation,
            stress=stress,
            novelty=novelty,
            attention=float(np.clip(arousal * 0.6 + mods.acetylcholine * 0.4, 0, 1)),
            sleep_pressure=0.0,
        )
        return {
            "vta_dopamine": mods.dopamine,
            "raphe_serotonin": mods.serotonin,
            "lc_norepinephrine": mods.norepinephrine,
            "accumbens": round(self.accumbens_activation, 3),
        }
