"""Proceso guardia de autonomía — auditoría decisiones integradas."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class AutonomyGuardProcess(BaseProcess):
    process_id: str = "autonomy_guard"
    period_ticks: int = 4
    priority: int = 62

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("autonomy_guard_mode") != "integrated":
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        store = context.state_store
        recent_actions = [
            ev for ev in store.event_log
            if ev.event_type == "action.selected" and ev.tick == tick
        ]
        legacy_forced = any(ev.payload.get("forced") for ev in recent_actions)
        return [
            CognitiveEvent(
                event_type="autonomy.guard",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "deliberation_authority": True,
                    "forced_blocked": legacy_forced,
                    "actions_this_tick": len(recent_actions),
                    "hud_selects_actions": False,
                },
            )
        ]
