"""Percepción activa — muestreo orientado por predicción."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ActivePerceptionPolicy:
    """Sesgo de muestreo hacia modalidades con alto error de predicción."""

    exploration_rate: float = 0.05

    def resample_weights(
        self,
        modalities: list[str],
        surprises: dict[str, float],
        rng: np.random.Generator,
    ) -> dict[str, float]:
        if not modalities:
            return {}
        base = {m: surprises.get(m, 0.1) + self.exploration_rate for m in modalities}
        total = sum(base.values()) or 1.0
        weights = {m: v / total for m, v in base.items()}
        if rng.random() < self.exploration_rate:
            pick = rng.choice(modalities)
            weights[pick] = weights.get(pick, 0.0) + 0.15
            total = sum(weights.values())
            weights = {m: v / total for m, v in weights.items()}
        return weights
