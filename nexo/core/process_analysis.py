"""Procesos Sprint 13 — huellas conductuales para análisis."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.behavioral.fingerprint import compute_behavior_fingerprint, metric_fingerprint_hash
from nexo.behavioral.metrics import compute_metrics
from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess


@dataclass
class BehavioralFingerprintProcess(BaseProcess):
    """Huella conductual periódica para análisis comparativo."""

    process_id: str = "behavioral_fingerprint"
    period_ticks: int = 30
    priority: int = 44

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        rt = context.config.get("_runtime_ref")
        if rt is None:
            return []
        partial = rt.build_result()
        metrics = compute_metrics(rt, partial)
        fp = compute_behavior_fingerprint(metrics, partial)
        fp["metric_hash"] = metric_fingerprint_hash(metrics)
        context.config["last_metric_fingerprint"] = fp["metric_hash"]
        tick = context.clock.tick
        return [
            CognitiveEvent(
                event_type="behavior.fingerprint",
                source=self.process_id,
                tick=tick,
                simulation_time=context.clock.simulation_time,
                payload=fp,
            )
        ]
