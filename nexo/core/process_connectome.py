"""Procesos Sprint 12 — entrega diferida connectome."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess


@dataclass
class ConnectomeDeliveryProcess(BaseProcess):
    """Emite eventos cuando el buffer entrega señales diferidas."""

    process_id: str = "connectome_delivery"
    period_ticks: int = 1
    priority: int = 98

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        deliveries = context.config.get("connectome_deliveries") or []
        if not deliveries:
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        events: list[CognitiveEvent] = []
        for source, target, vec in deliveries:
            events.append(
                CognitiveEvent(
                    event_type="connectome.signal_delivered",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={
                        "source": source,
                        "target": target,
                        "norm": round(float(np.linalg.norm(vec)), 5),
                    },
                )
            )
        return events
