"""Enrutamiento de señales a través del conectoma."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from nexo.connectome.connection import Connection
from nexo.connectome.graph import ConnectomeGraph
from nexo.connectome.latency_buffer import LatencyBuffer
from nexo.connectome.plastic_connectivity import PlasticityState
from nexo.interventions.lesion import LesionState


@dataclass
class ConnectomeRouter:
    graph: ConnectomeGraph
    plasticity: PlasticityState = field(default_factory=PlasticityState)
    lesions: LesionState = field(default_factory=LesionState)
    latency_buffer: LatencyBuffer = field(default_factory=LatencyBuffer)
    latency_enabled: bool = False
    attention_gate: float = 1.0
    current_tick: int = 0
    rng: Any | None = None

    def advance_tick(self, tick: int) -> list[tuple[str, str, np.ndarray]]:
        """Entrega señales pendientes y actualiza tick corriente."""
        self.current_tick = tick
        return self.latency_buffer.flush(tick)

    def route(
        self,
        source: str,
        target: str,
        signal: tuple[float, ...] | np.ndarray,
        salience: float = 1.0,
    ) -> np.ndarray:
        vec = np.asarray(signal, dtype=np.float64)
        if self.lesions.is_severed(source, target):
            return np.zeros_like(vec)
        conn = self._find_connection(source, target)
        if conn is None:
            return vec
        gate = max(conn.minimum_gate, self.attention_gate * salience)
        if conn.gating_modulator == "attention":
            gate = max(conn.minimum_gate, self.attention_gate)
        w = conn.effective_weight(gate)
        w *= self.plasticity.get_weight(source, target, conn.weight)
        w *= self.lesions.scale_for(source, target)
        w *= conn.reliability
        if conn.noise > 0 and self.rng is not None:
            w *= 1.0 + float(self.rng.normal(0, conn.noise))

        latency = self.lesions.effective_latency(source, target, conn.latency_ticks)
        weighted = vec * w
        if self.latency_enabled and latency > 0:
            self.latency_buffer.enqueue(
                deliver_tick=self.current_tick + latency,
                source=source,
                target=target,
                signal=vec,
                weight=w,
            )
            return np.zeros_like(vec)
        return weighted

    def _find_connection(self, source: str, target: str) -> Connection | None:
        for c in self.graph.connections:
            if c.source == source and c.target == target:
                return c
        return None

    def propagate(self, source: str, signal: np.ndarray, salience: float = 1.0) -> dict[str, np.ndarray]:
        out: dict[str, np.ndarray] = {}
        for conn in self.graph.outgoing(source):
            out[conn.target] = self.route(source, conn.target, signal, salience)
        return out
