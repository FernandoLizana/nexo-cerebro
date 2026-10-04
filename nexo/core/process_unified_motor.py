"""Proceso motor unificado — registra autoridad integrada."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class UnifiedMotorProcess(BaseProcess):
    process_id: str = "unified_motor"
    period_ticks: int = 1
    priority: int = 58

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("unified_motor_mode") != "integrated":
            return []
        brain = context.legacy_brain
        tick = context.clock.tick
        t = context.clock.simulation_time
        selected = [
            ev for ev in context.state_store.event_log
            if ev.event_type == "action.selected" and ev.tick == tick
        ]
        integrated_action = ""
        confidence = 0.0
        if selected:
            integrated_action = str(selected[-1].payload.get("action", ""))
            confidence = float(selected[-1].payload.get("confidence", 0.0))
        legacy_key = ""
        if brain is not None:
            legacy_key = str(getattr(brain.deliberation.last, "choice_key", "") or "")
        return [
            CognitiveEvent(
                event_type="unified.motor",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "motor_authority": "integrated",
                    "integrated_action": integrated_action,
                    "legacy_choice_key": legacy_key,
                    "confidence": confidence,
                    "agreement": integrated_action == legacy_key if integrated_action and legacy_key else False,
                },
            )
        ]
