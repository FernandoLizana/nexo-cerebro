"""Proceso de auditoría deliberación integrado vs legacy."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class DeliberationBridgeAuditProcess(BaseProcess):
    """Registra acuerdo/desacuerdo entre BG integrado y sugerencia legacy."""

    process_id: str = "deliberation_bridge_audit"
    period_ticks: int = 1
    priority: int = 59

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("deliberation_bridge_mode") != "integrated":
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        recent = [ev for ev in context.state_store.event_log if ev.tick == tick]
        integrated = next(
            (
                ev for ev in reversed(recent)
                if ev.event_type == "action.selected" and not ev.payload.get("legacy")
            ),
            None,
        )
        legacy = next(
            (
                ev for ev in reversed(recent)
                if ev.event_type == "action.selected" and ev.payload.get("legacy")
            ),
            None,
        )
        if integrated is None and legacy is None:
            return []
        integrated_action = integrated.payload.get("action") if integrated else None
        legacy_action = legacy.payload.get("action") if legacy else None
        return [
            CognitiveEvent(
                event_type="deliberation.bridge",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "integrated_action": integrated_action,
                    "legacy_action": legacy_action,
                    "agreement": integrated_action == legacy_action,
                    "authority": "integrated",
                },
            )
        ]
