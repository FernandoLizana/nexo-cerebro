"""Procesos cognitivos Sprint 2 — cuerpo y homeostasis."""

from __future__ import annotations

from dataclasses import dataclass, field

from nexo.body.interoception import InteroceptiveChannel
from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess
from nexo.homeostasis.allostasis import AllostaticController
from nexo.homeostasis.controller import HomeostaticController
from nexo.homeostasis.drives import DriveField


@dataclass
class MetabolismProcess(BaseProcess):
    """Metabolismo basal + actualización de drives competitivos."""

    process_id: str = "metabolism"
    period_ticks: int = 1
    priority: int = 86

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        controller: HomeostaticController | None = context.config.get("homeostatic_controller")
        if controller is None:
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        events = controller.basal_events(tick=tick, simulation_time=t, source=self.process_id)

        world = context.config.get("world_state")
        expected_danger = float(getattr(world, "danger_level", 0.0)) if world else 0.0
        drives = DriveField.from_body(controller.body, expected_danger=expected_danger)
        context.config["drives"] = drives

        if world is not None and hasattr(world, "sync_from_body"):
            world.sync_from_body(controller.body)

        return events


@dataclass
class AllostasisProcess(BaseProcess):
    """Anticipación alostática — actualiza metas según tendencias corporales."""

    process_id: str = "allostasis"
    period_ticks: int = 10
    priority: int = 75
    controller: AllostaticController = field(default_factory=AllostaticController)

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        hctrl: HomeostaticController | None = context.config.get("homeostatic_controller")
        if hctrl is None:
            return []
        return self.controller.goal_events(
            hctrl.body,
            tick=context.clock.tick,
            simulation_time=context.clock.simulation_time,
            source=self.process_id,
        )


@dataclass
class BodyInteroceptionProcess(BaseProcess):
    """Interocepción imperfecta del estado corporal."""

    process_id: str = "interoception"
    period_ticks: int = 2
    priority: int = 80
    channel: InteroceptiveChannel = field(default_factory=InteroceptiveChannel)

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        hctrl: HomeostaticController | None = context.config.get("homeostatic_controller")
        if hctrl is None:
            return []
        body = hctrl.body
        tick = context.clock.tick
        t = context.clock.simulation_time
        perceived = self.channel.read_vector(
            body.to_homeostatic_dict(),
            context.rng,
            stress=body.stress_load,
            threat=body.pain,
        )
        return [
            CognitiveEvent(
                event_type="perception.updated",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "modality": "interoception",
                    "embedding": perceived,
                    "salience": 0.25 + body.pain * 0.5 + (1.0 - perceived[0]) * 0.2,
                    "uncertainty": self.channel.noise_std,
                },
            )
        ]
