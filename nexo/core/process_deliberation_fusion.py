"""Proceso de fusión deliberación — resuelve conflictos con autoridad integrada."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.behavioral.deliberation_fusion import FUSION_POLICY
from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class DeliberationFusionProcess(BaseProcess):
    """Emite decisión fusionada cuando bridge detecta desacuerdo integrado/legacy."""

    process_id: str = "deliberation_fusion"
    period_ticks: int = 1
    priority: int = 58

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("deliberation_fusion_mode") != "integrated":
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        recent = [ev for ev in context.state_store.event_log if ev.tick == tick]
        bridge = next((ev for ev in reversed(recent) if ev.event_type == "deliberation.bridge"), None)
        if bridge is None:
            return []
        integrated_action = bridge.payload.get("integrated_action")
        legacy_action = bridge.payload.get("legacy_action")
        agreement = bridge.payload.get("agreement", False)
        resolved = integrated_action if integrated_action else legacy_action
        return [
            CognitiveEvent(
                event_type="deliberation.fusion",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "integrated_action": integrated_action,
                    "legacy_action": legacy_action,
                    "resolved_action": resolved,
                    "agreement": agreement,
                    "fusion_policy": FUSION_POLICY,
                    "authority": "integrated",
                },
            )
        ]
