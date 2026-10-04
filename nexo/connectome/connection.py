"""Conexión dirigida entre módulos cognitivos."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Connection:
    source: str
    target: str
    signal_type: str
    weight: float = 1.0
    latency_ticks: int = 1
    excitatory: bool = True
    plastic: bool = False
    bandwidth: float = 1.0
    noise: float = 0.0
    reliability: float = 1.0
    minimum_gate: float = 0.0
    gating_modulator: str | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not 0.0 <= self.weight <= 2.0:
            errors.append(f"weight_out_of_range:{self.weight}")
        if self.latency_ticks < 0:
            errors.append("negative_latency")
        if not 0.0 <= self.reliability <= 1.0:
            errors.append("reliability_out_of_range")
        return errors

    def effective_weight(self, gate: float = 1.0) -> float:
        w = self.weight * gate
        return w if self.excitatory else -abs(w)
