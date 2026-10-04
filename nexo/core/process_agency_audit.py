"""Emite auditoría agency post-certificado (Fase 15)."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.behavioral.agency_audit import summarize_agency_audit
from nexo.core.events import CognitiveEvent
from nexo.core.process import BaseProcess, ProcessContext


@dataclass
class AgencyAuditProcess(BaseProcess):
    process_id: str = "agency_audit"
    period_ticks: int = 4
    priority: int = 49

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        if context.config.get("agency_audit_mode") != "integrated":
            return []
        runtime = context.config.get("_runtime_ref")
        if runtime is None:
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        summary = summarize_agency_audit(runtime)
        return [
            CognitiveEvent(
                event_type="agency.audit",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "agency_score": summary["agency_score"],
                    "certificate_score": summary["certificate_score"],
                    "agency_valid_certificates": summary["agency_valid_certificates"],
                    "forced_blocked_count": summary["forced_blocked_count"],
                },
            )
        ]
