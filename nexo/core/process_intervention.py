"""Procesos Sprint 11 — auditoría de lesiones connectome."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess


@dataclass
class ConnectomeLesionAuditProcess(BaseProcess):
    """Emite lesiones activas al inicio de la simulación."""

    process_id: str = "connectome_lesion_audit"
    period_ticks: int = 1
    priority: int = 99
    _emitted: bool = False

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if self._emitted:
            return []
        lesions = context.router.lesions
        active = lesions.active_lesions()
        if not active:
            self._emitted = True
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        events = [
            CognitiveEvent(
                event_type="connectome.lesion_applied",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload=entry,
            )
            for entry in active
        ]
        self._emitted = True
        return events
