"""Procesos Sprint 10 — evaluación conductual en runtime."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.behavioral.metrics import compute_metrics
from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess


@dataclass
class BehavioralSnapshotProcess(BaseProcess):
    """Snapshot periódico de métricas conductuales."""

    process_id: str = "behavioral_snapshot"
    period_ticks: int = 20
    priority: int = 45

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        rt = context.config.get("_runtime_ref")
        if rt is None:
            return []
        partial = rt.build_result()
        metrics = compute_metrics(rt, partial)
        tick = context.clock.tick
        return [
            CognitiveEvent(
                event_type="behavior.snapshot",
                source=self.process_id,
                tick=tick,
                simulation_time=context.clock.simulation_time,
                payload={k: round(v, 5) if isinstance(v, float) else v for k, v in metrics.items()},
            )
        ]
