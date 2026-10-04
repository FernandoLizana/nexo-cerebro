"""Proceso deliberación unificada — escribe acción motora fusionada."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.behavioral.deliberation_unified import resolve_unified_action
from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class DeliberationUnifiedProcess(BaseProcess):
    """Resuelve integrado+legacy y emite action.unified antes del cerebelo/motor."""

    process_id: str = "deliberation_unified"
    period_ticks: int = 1
    priority: int = 57

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("deliberation_unified_mode") != "integrated":
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        integrated_ev = next(
            (
                ev for ev in reversed(context.state_store.event_log)
                if ev.tick == tick
                and ev.event_type == "action.selected"
                and not ev.payload.get("legacy")
            ),
            None,
        )
        if integrated_ev is None:
            return []
        resolution = resolve_unified_action(context.state_store.event_log, tick=tick)
        resolved = resolution["resolved_action"]
        if not resolved:
            return []
        return [
            CognitiveEvent(
                event_type="action.unified",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    **resolution,
                    "action": resolved,
                    "confidence": float(integrated_ev.payload.get("confidence", 0.5)),
                },
            )
        ]
