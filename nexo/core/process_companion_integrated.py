"""Proceso compañera Nira integrada — proximidad y dyad advisory."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.behavioral.companion_integrated import IntegratedCompanionState, companion_from_legacy
from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class CompanionIntegratedProcess(BaseProcess):
    process_id: str = "companion_integrated"
    period_ticks: int = 5
    priority: int = 35

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("companion_integrated_mode") != "integrated":
            return []
        runtime = context.config.get("_runtime_ref")
        if runtime is None:
            return []
        state: IntegratedCompanionState = context.config.get("companion_state")
        if state is None:
            state = companion_from_legacy(runtime) or IntegratedCompanionState()
            context.config["companion_state"] = state
        world = runtime.world
        agent_x = float(getattr(world, "agent_x", 0.0))
        w2 = getattr(world, "_world2d", None)
        if w2 is not None:
            agent_x = float(w2.agent_x)
            agent_y = float(w2.agent_y)
        else:
            agent_y = 230.0
        dist = ((state.x - agent_x) ** 2 + (state.y - agent_y) ** 2) ** 0.5
        proximate = dist < 120.0
        if proximate:
            state.proximity_ticks += 1
            state.bond = min(1.0, state.bond + 0.002)
        tick = context.clock.tick
        t = context.clock.simulation_time
        events: list[CognitiveEvent] = []
        if proximate and tick % 5 == 0:
            state.dyad_events += 1
            events.append(
                CognitiveEvent(
                    event_type="companion.dyad",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={
                        "name": state.name,
                        "distance": round(dist, 1),
                        "bond": round(state.bond, 3),
                        "proximate": True,
                    },
                )
            )
        return events
