"""Proceso auditoría roadmap100 en legacy brain."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.behavioral.roadmap100_bridge import count_roadmap100_flags
from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class Roadmap100BridgeProcess(BaseProcess):
    process_id: str = "roadmap100_bridge"
    period_ticks: int = 5
    priority: int = 38

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("roadmap100_bridge_mode") != "integrated":
            return []
        brain = context.legacy_brain
        if brain is None:
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        flags = count_roadmap100_flags(getattr(brain, "experiment_flags", None))
        return [
            CognitiveEvent(
                event_type="roadmap100.bridge",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "enabled_count": flags.get("enabled_count", 0),
                    "coverage": flags.get("coverage", 0.0),
                    "catalog_size": flags.get("catalog_size", 0),
                },
            )
        ]
