"""Procesos Sprint 15 — trazabilidad integrada."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess
from nexo.telemetry.integrated_trace import IntegratedTraceCollector


@dataclass
class IntegratedTraceProcess(BaseProcess):
    """Captura traza compacta por tick cuando tracing_mode está activo."""

    process_id: str = "integrated_trace"
    period_ticks: int = 1
    priority: int = 43

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        collector: IntegratedTraceCollector | None = context.config.get("trace_collector")
        if collector is None:
            return []
        state = context.state_store.state
        deliveries = context.config.get("connectome_deliveries") or []
        collector.record_tick(
            tick=context.clock.tick,
            action=state.current_action,
            energy=state.homeostatic.energy,
            deliveries=len(deliveries),
            config=context.config,
        )
        tick = context.clock.tick
        return [
            CognitiveEvent(
                event_type="telemetry.trace",
                source=self.process_id,
                tick=tick,
                simulation_time=context.clock.simulation_time,
                payload={
                    "action": state.current_action,
                    "energy": round(float(state.homeostatic.energy), 5),
                    "deliveries": len(deliveries),
                },
            )
        ]
