"""Proceso auditoría puente Flask demo."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.behavioral.flask_demo_bridge import build_flask_bridge_payload
from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class FlaskDemoBridgeProcess(BaseProcess):
    process_id: str = "flask_demo_bridge"
    period_ticks: int = 6
    priority: int = 37

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("flask_demo_bridge_mode") != "integrated":
            return []
        runtime = context.config.get("_runtime_ref")
        if runtime is None:
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        payload = build_flask_bridge_payload(runtime)
        return [
            CognitiveEvent(
                event_type="flask.bridge",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "legacy_attached": payload["legacy_brain_attached"],
                    "hud_ready": payload["hud_ready"],
                    "furniture_count": payload["furniture_count"],
                },
            )
        ]
