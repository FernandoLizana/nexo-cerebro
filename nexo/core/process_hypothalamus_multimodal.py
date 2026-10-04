"""Proceso hipotálamo multimodal — advisory hacia neuromoduladores."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.behavioral.hypothalamus_multimodal import fuse_multimodal_signals
from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class HypothalamusMultimodalProcess(BaseProcess):
    process_id: str = "hypothalamus_multimodal"
    period_ticks: int = 3
    priority: int = 39

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("hypothalamus_multimodal_mode") != "integrated":
            return []
        runtime = context.config.get("_runtime_ref")
        if runtime is None:
            return []
        fused = fuse_multimodal_signals(runtime)
        mods = context.config.get("modulators")
        if mods is not None:
            mods.dopamine = 0.7 * mods.dopamine + 0.3 * fused["dopamine"]
            if hasattr(mods, "norepinephrine"):
                mods.norepinephrine = 0.7 * mods.norepinephrine + 0.3 * fused["cortisol"]
            if hasattr(mods, "serotonin"):
                mods.serotonin = 0.7 * mods.serotonin + 0.3 * fused["oxytocin"]
        tick = context.clock.tick
        t = context.clock.simulation_time
        return [
            CognitiveEvent(
                event_type="hypothalamus.multimodal",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload=fused,
            )
        ]
