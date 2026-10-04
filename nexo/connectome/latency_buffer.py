"""Buffer temporal de señales connectome con latencia de aristas."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class PendingSignal:
    deliver_tick: int
    source: str
    target: str
    signal: np.ndarray
    weight: float


@dataclass
class LatencyBuffer:
    """Cola de entrega diferida por tick de simulación."""

    pending: list[PendingSignal] = field(default_factory=list)
    delivered: dict[tuple[str, str], np.ndarray] = field(default_factory=dict)
    last_deliveries: list[tuple[str, str, np.ndarray]] = field(default_factory=list)
    total_delivered: int = 0

    def enqueue(
        self,
        *,
        deliver_tick: int,
        source: str,
        target: str,
        signal: np.ndarray,
        weight: float,
    ) -> None:
        self.pending.append(
            PendingSignal(
                deliver_tick=deliver_tick,
                source=source,
                target=target,
                signal=np.asarray(signal, dtype=np.float64).copy(),
                weight=weight,
            )
        )

    def flush(self, tick: int) -> list[tuple[str, str, np.ndarray]]:
        due = [p for p in self.pending if p.deliver_tick <= tick]
        self.pending = [p for p in self.pending if p.deliver_tick > tick]
        self.last_deliveries = []
        for pending in due:
            vec = pending.signal * pending.weight
            key = (pending.source, pending.target)
            self.delivered[key] = vec
            self.last_deliveries.append((pending.source, pending.target, vec))
            self.total_delivered += 1
        return self.last_deliveries

    def get_delivered(self, source: str, target: str) -> np.ndarray | None:
        return self.delivered.get((source, target))
