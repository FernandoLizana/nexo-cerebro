"""Proceso auditoría bloque E roadmap100."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.behavioral.roadmap100_e_block import audit_e_block_conditions
from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class Roadmap100EBlockProcess(BaseProcess):
    process_id: str = "roadmap100_e_block"
    period_ticks: int = 10
    priority: int = 37

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("roadmap100_e_block_mode") != "integrated":
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        audit = audit_e_block_conditions()
        return [
            CognitiveEvent(
                event_type="roadmap100.e_block",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "coverage": audit["coverage"],
                    "resolved_count": audit["resolved_count"],
                    "catalog_size": audit["catalog_size"],
                },
            )
        ]
