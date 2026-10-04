"""Proceso legacy adapter con prioridad temprana (61 > BG 60)."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class LegacyEarlyBrainAdapterProcess(BaseProcess):
    """Ejecuta InfantApeBrain antes de la selección integrada."""

    process_id: str = "legacy_brain_adapter_early"
    period_ticks: int = 1
    priority: int = 61

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("legacy_adapter_early_mode") != "integrated":
            return []
        brain = context.legacy_brain
        if brain is None:
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        try:
            if context.config.get("suppress_legacy_world_tick"):
                delib = brain.deliberation.last
                out = {
                    "deliberation": {
                        "choice_key": delib.choice_key,
                        "agency": delib.agency,
                    }
                }
            else:
                out = brain.world_tick(steps=1)
        except Exception:
            return []
        delib = out.get("deliberation") or {}
        events: list[CognitiveEvent] = []
        if delib.get("choice_key"):
            events.append(
                CognitiveEvent(
                    event_type="action.selected",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={
                        "action": str(delib["choice_key"]),
                        "confidence": float(delib.get("agency", 0.5)),
                        "candidates": (str(delib["choice_key"]),),
                        "legacy": True,
                        "early": True,
                    },
                )
            )
        return events
