"""Procesos Sprint 7 — workspace global y metacognición."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess
from nexo.homeostasis.drives import DriveField
from nexo.interventions.routing_helpers import route_gain
from nexo.metacognition.monitor import MetacognitiveMonitor
from nexo.workspace.global_workspace import GlobalWorkspace


@dataclass
class GlobalWorkspaceProcess(BaseProcess):
    """Integración de candidatos y broadcast al workspace global."""

    process_id: str = "global_workspace"
    period_ticks: int = 3
    priority: int = 67

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        workspace: GlobalWorkspace = context.config.setdefault("global_workspace", GlobalWorkspace())
        drives: DriveField | None = context.config.get("drives")
        state = context.state_store.state
        tick = context.clock.tick
        t = context.clock.simulation_time

        percepts = [
            ev.payload
            for ev in context.state_store.event_log[-20:]
            if ev.event_type == "perception.updated"
        ]
        candidates = workspace.gather_from_events(
            percepts=percepts,
            drives=drives.drives if drives else {},
            focus=state.attention_focus,
            energy=state.homeostatic.energy,
        )
        winners = workspace.select_winners(candidates)
        bias = workspace.action_bias()
        routing_mode = context.config.get("routing_mode", "legacy")
        if routing_mode == "integrated":
            ws_gain = route_gain(
                context.router,
                "global_workspace",
                "prefrontal",
                (float(len(winners)), float(len(candidates)), state.homeostatic.energy),
            )
            bias = {k: v * ws_gain for k, v in bias.items()}
            context.config["connectome_workspace_route_gain"] = ws_gain
        context.config["workspace_action_bias"] = bias
        context.config["workspace_winners"] = winners

        content = workspace.broadcast_labels()
        return [
            CognitiveEvent(
                event_type="workspace.broadcast",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "content": content,
                    "winners": [w.to_dict() for w in winners],
                    "suppressed": workspace.suppressed_count,
                    "action_bias": {k: round(v, 4) for k, v in bias.items()},
                },
            )
        ]


@dataclass
class MetacognitionProcess(BaseProcess):
    """Monitoreo metacognitivo de claridad, duda y agencia."""

    process_id: str = "metacognition"
    period_ticks: int = 5
    priority: int = 64

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        monitor: MetacognitiveMonitor = context.config.setdefault(
            "metacognitive_monitor", MetacognitiveMonitor()
        )
        workspace: GlobalWorkspace | None = context.config.get("global_workspace")
        deliberation = context.config.get("deliberation_result")
        surprises = context.config.get("surprises") or {}
        state = context.state_store.state
        tick = context.clock.tick
        t = context.clock.simulation_time

        winner_sal = workspace.winners[0].salience if workspace and workspace.winners else 0.2
        total_sal = sum(w.salience for w in workspace.winners) if workspace and workspace.winners else 0.5
        conflict = float(getattr(deliberation, "conflict", 0.0)) if deliberation else 0.0
        delib_conf = float(getattr(deliberation, "confidence", 0.5)) if deliberation else 0.5
        pfc_veto = bool(getattr(deliberation, "pfc_veto", False)) if deliberation else False
        mean_surprise = float(sum(surprises.values()) / len(surprises)) if surprises else 0.0

        meta = monitor.evaluate(
            winner_salience=winner_sal,
            total_salience=total_sal,
            conflict=conflict,
            surprise=mean_surprise,
            sleep_pressure=state.homeostatic.sleep_pressure,
            deliberation_confidence=delib_conf,
            pfc_veto=pfc_veto,
        )
        context.config["metacognition"] = meta

        return [
            CognitiveEvent(
                event_type="metacognition.updated",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload=meta.to_dict(),
            )
        ]
