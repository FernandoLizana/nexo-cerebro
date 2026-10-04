"""Paquetes sensoriales y relay talámico."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SensoryPacket:
    modality: str
    embedding: tuple[float, ...]
    salience: float
    source: str = "sensory_hub"


@dataclass(frozen=True)
class GatedSignal:
    modality: str
    embedding: tuple[float, ...]
    gain: float
    suppressed: bool


@dataclass
class ThalamicRelay:
    """Relay sensorial con competencia contextual — no simple umbral."""

    minimum_gate: float = 0.15

    def relay(
        self,
        packets: list[SensoryPacket],
        *,
        context_gain: float,
        reticular_mask: dict[str, float],
    ) -> list[GatedSignal]:
        if not packets:
            return []
        scored: list[tuple[float, SensoryPacket]] = []
        for p in packets:
            mask = reticular_mask.get(p.modality, 1.0)
            score = p.salience * context_gain * mask
            scored.append((score, p))
        scored.sort(key=lambda x: -x[0])
        max_score = scored[0][0] if scored else 1.0
        out: list[GatedSignal] = []
        for score, p in scored:
            gain = score / max(max_score, 1e-6)
            suppressed = gain < self.minimum_gate
            if suppressed:
                gain = self.minimum_gate * 0.5
            out.append(
                GatedSignal(
                    modality=p.modality,
                    embedding=p.embedding,
                    gain=float(gain),
                    suppressed=suppressed,
                )
            )
        return out
