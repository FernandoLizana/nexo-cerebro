"""Estimación de precisión sensorial."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PrecisionEstimator:
    """Precisión modulada por atención, modalidad y ruido ambiental."""

    base_precision: float = 0.5
    attention_boost: float = 0.25
    threat_boost: float = 0.15
    noise_floor: float = 0.08

    def estimate(
        self,
        *,
        salience: float,
        modality: str,
        attention_focus: tuple[str, ...],
        noise: float = 0.0,
        stress: float = 0.0,
    ) -> float:
        p = self.base_precision + salience * 0.35
        if modality in attention_focus:
            p += self.attention_boost
        if modality == "danger":
            p += self.threat_boost
        p *= 1.0 - min(0.4, stress * 0.3)
        p = p / (1.0 + noise + self.noise_floor)
        return max(0.1, min(1.0, p))
