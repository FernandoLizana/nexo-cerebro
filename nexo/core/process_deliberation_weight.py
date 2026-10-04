"""Proceso deliberación con peso legacy configurable."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.behavioral.deliberation_weight import resolve_weighted_action
from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class DeliberationWeightProcess(BaseProcess):
    """Emite action.weighted cuando deliberation_weight_mode está activo."""

    process_id: str = "deliberation_weight"
    period_ticks: int = 1
    priority: int = 56

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("deliberation_weight_mode") != "integrated":
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
        weight = float(context.config.get("legacy_advisory_weight", 0.0))
        resolution = resolve_weighted_action(
            context.state_store.event_log,
            tick=tick,
            legacy_weight=weight,
        )
        resolved = resolution["resolved_action"]
        if not resolved:
            return []
        return [
            CognitiveEvent(
                event_type="action.weighted",
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
