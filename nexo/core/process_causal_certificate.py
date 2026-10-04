"""Emite certificado causal por tick (Fase 14)."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.behavioral.causal_certificate import build_causal_certificate
from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class CausalCertificateProcess(BaseProcess):
    process_id: str = "causal_certificate"
    period_ticks: int = 1
    priority: int = 50

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("causal_certificate_mode") != "integrated":
            return []
        runtime = context.config.get("_runtime_ref")
        if runtime is None:
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        cert = build_causal_certificate(runtime, tick=tick)
        return [
            CognitiveEvent(
                event_type="causal.certificate",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload=cert,
            )
        ]
