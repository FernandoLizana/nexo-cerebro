"""Proceso auditoría sincronización World3D."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.demo.world3d_sync import extract_game3d_state, game3d_fidelity_score
from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class World3DSyncProcess(BaseProcess):
    process_id: str = "world3d_sync"
    period_ticks: int = 8
    priority: int = 36

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("world3d_sync_mode") != "integrated":
            return []
        runtime = context.config.get("_runtime_ref")
        if runtime is None:
            return []
        state = extract_game3d_state(runtime.world)
        fidelity = game3d_fidelity_score(state)
        tick = context.clock.tick
        t = context.clock.simulation_time
        return [
            CognitiveEvent(
                event_type="world3d.sync",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "fidelity": fidelity,
                    "furniture_count": len(state.get("furniture") or []),
                    "room": state.get("room", ""),
                },
            )
        ]
