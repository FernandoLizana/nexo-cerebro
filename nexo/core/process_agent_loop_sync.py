"""Proceso auditoría agent_loop_sync."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext
from nexo.demo.agent_loop_sync import run_agent_loop_lite_sync


@dataclass
class AgentLoopSyncProcess(BaseProcess):
    process_id: str = "agent_loop_sync"
    period_ticks: int = 1
    priority: int = 64

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("agent_loop_sync_mode") != "integrated":
            return []
        if context.config.get("unified_motor_mode") != "integrated":
            return []
        brain = context.legacy_brain
        if brain is None:
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        lite = run_agent_loop_lite_sync(brain)
        return [
            CognitiveEvent(
                event_type="agent_loop.sync",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "lite_sync": bool(lite.get("synced")),
                    "phases": lite.get("phases", []),
                    "thought_len": lite.get("thought_len", 0),
                    "companion_events": lite.get("companion_events", 0),
                },
            )
        ]
