"""Procesos Sprint 14 — auditoría de enrutamiento connectome ampliado."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess

EXTENDED_ROUTES = (
    ("hippocampus", "prefrontal"),
    ("global_workspace", "prefrontal"),
    ("working_memory", "prefrontal"),
)


@dataclass
class ConnectomeRoutingAuditProcess(BaseProcess):
    """Registra rutas extendidas activas al inicio."""

    process_id: str = "connectome_routing_audit"
    period_ticks: int = 1
    priority: int = 97
    _emitted: bool = False

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if self._emitted:
            return []
        if context.config.get("routing_mode") != "integrated":
            self._emitted = True
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        events = [
            CognitiveEvent(
                event_type="connectome.routing_active",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={"source": src, "target": tgt},
            )
            for src, tgt in EXTENDED_ROUTES
        ]
        self._emitted = True
        return events
