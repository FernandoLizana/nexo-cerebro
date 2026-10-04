"""Interocepción con ruido, sesgo e incertidumbre."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class InteroceptiveSignal:
    variable: str
    true_value: float
    perceived_value: float
    uncertainty: float
    latency_ticks: int = 0


@dataclass
class InteroceptiveChannel:
    """Canal interoceptivo imperfecto — no acceso directo al cuerpo."""

    noise_std: float = 0.04
    bias: float = 0.0
    attention_gain: float = 1.0
    threat_amplification: float = 0.15
    _pending: list[InteroceptiveSignal] = field(default_factory=list)

    def perceive(
        self,
        *,
        variable: str,
        true_value: float,
        rng: np.random.Generator,
        stress: float = 0.0,
        threat: float = 0.0,
        latency: int = 1,
    ) -> InteroceptiveSignal:
        noise = float(rng.normal(0.0, self.noise_std))
        bias = self.bias
        if variable == "pain" and threat > 0.2:
            bias += self.threat_amplification * threat
        if variable == "energy" and stress > 0.4:
            bias -= 0.05  # ansiedad puede confundirse con hambre (subestima energía)
        perceived = max(0.0, min(1.0, true_value + bias + noise * self.attention_gain))
        uncertainty = min(1.0, self.noise_std * 2 + abs(bias) + stress * 0.1)
        sig = InteroceptiveSignal(
            variable=variable,
            true_value=true_value,
            perceived_value=perceived,
            uncertainty=uncertainty,
            latency_ticks=latency,
        )
        self._pending.append(sig)
        return sig

    def read_vector(
        self,
        values: dict[str, float],
        rng: np.random.Generator,
        *,
        stress: float = 0.0,
        threat: float = 0.0,
    ) -> tuple[float, float, float]:
        e = self.perceive(variable="energy", true_value=values["energy"], rng=rng, stress=stress)
        f = self.perceive(variable="fatigue", true_value=values["fatigue"], rng=rng, stress=stress)
        p = self.perceive(
            variable="pain", true_value=values["pain"], rng=rng, stress=stress, threat=threat
        )
        return e.perceived_value, f.perceived_value, p.perceived_value
