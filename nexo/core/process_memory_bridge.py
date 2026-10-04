"""Proceso auditoría memory_bridge."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext
from nexo.demo.memory_bridge import sync_memory_bridge_advisory


@dataclass
class MemoryBridgeProcess(BaseProcess):
    process_id: str = "memory_bridge"
    period_ticks: int = 3
    priority: int = 41

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("memory_bridge_mode") != "integrated":
            return []
        brain = context.legacy_brain
        runtime = context.config.get("_runtime_ref")
        if brain is None or runtime is None:
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        stats = sync_memory_bridge_advisory(brain, runtime)
        return [
            CognitiveEvent(
                event_type="memory.bridge",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload=stats,
            )
        ]
