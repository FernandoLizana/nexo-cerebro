"""Procesos Sprint 5 — PFC, ganglios basales, cerebelo y planificación."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from nexo.basal_ganglia.gate import ActionGate
from nexo.cerebellum.coordinator import CerebellarCoordinator
from nexo.core.environment_protocol import action_schemas_for
from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess
from nexo.homeostasis.drives import DriveField
from nexo.interventions.routing_helpers import route_gain
from nexo.planning.goal_stack import GoalStack
from nexo.prefrontal.deliberation import PrefrontalDeliberator


@dataclass
class GoalStackProcess(BaseProcess):
    """Planificación multi-paso desde drives homeostáticos."""

    process_id: str = "goal_stack"
    period_ticks: int = 5
    priority: int = 71
    hunger_plan_threshold: float = 0.45
    safety_plan_threshold: float = 0.55

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        stack: GoalStack = context.config.setdefault("goal_stack", GoalStack())
        drives: DriveField | None = context.config.get("drives")
        tick = context.clock.tick
        t = context.clock.simulation_time
        events: list[CognitiveEvent] = []

        recent_action = next(
            (
                ev.payload.get("action")
                for ev in reversed(context.state_store.event_log[-6:])
                if ev.event_type == "action.selected"
            ),
            None,
        )
        if recent_action and stack.advance_if_matched(str(recent_action)):
            events.append(
                CognitiveEvent(
                    event_type="plan.step_advanced",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={"action": recent_action, "depth": stack.depth()},
                )
            )

        if drives is not None and stack.depth() == 0:
            if drives.drives.get("hunger", 0.0) >= self.hunger_plan_threshold:
                stack.push_plan("eat")
            elif drives.drives.get("safety", 0.0) >= self.safety_plan_threshold:
                stack.push_plan("flee")

        if stack.depth() > 0:
            events.append(
                CognitiveEvent(
                    event_type="plan.updated",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={
                        "goals": stack.goal_labels(),
                        "plan_action": stack.peek_action(),
                        "depth": stack.depth(),
                    },
                )
            )
            events.append(
                CognitiveEvent(
                    event_type="goals.updated",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={"goals": ("survive",) + stack.goal_labels()},
                )
            )
        return events


@dataclass
class PrefrontalDeliberationProcess(BaseProcess):
    """Deliberación PFC — competencia límbica vs ejecutiva."""

    process_id: str = "prefrontal_deliberation"
    period_ticks: int = 5
    priority: int = 63

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        world = context.config.get("world_state")
        if world is None:
            return []
        deliberator: PrefrontalDeliberator = context.config.setdefault(
            "prefrontal_deliberator", PrefrontalDeliberator()
        )
        gate: ActionGate = context.config.get("action_gate")
        stack: GoalStack | None = context.config.get("goal_stack")
        drives: DriveField | None = context.config.get("drives")
        state = context.state_store.state
        tick = context.clock.tick
        t = context.clock.simulation_time

        habit_bias = gate.habits if gate else {}
        try:
            schemas = action_schemas_for(world)
        except Exception:
            schemas = None
        result = deliberator.run(
            candidates=world.available_actions(),
            drives=drives.drives if drives else {},
            wm_items={k: v for k, v in state.working_memory_items},
            goals=state.active_goals,
            plan_action=stack.peek_action() if stack else None,
            energy=state.homeostatic.energy,
            safety_need=state.homeostatic.safety_need,
            habit_bias=habit_bias,
            workspace_bias=context.config.get("workspace_action_bias"),
            action_schemas=schemas,
            goal_relevance=context.config.get("goal_relevance"),
            persona_modifiers=context.config.get("persona_modifiers"),
        )
        context.config["deliberation_result"] = result

        return [
            CognitiveEvent(
                event_type="deliberation.completed",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload=result.to_payload(),
            )
        ]


@dataclass
class EnhancedBasalGangliaProcess(BaseProcess):
    """Ganglios basales con hábito, deliberación PFC y memoria episódica."""

    process_id: str = "basal_ganglia_integrated"
    period_ticks: int = 1
    priority: int = 60

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        world = context.config.get("world_state")
        if world is None:
            return []
        gate: ActionGate = context.config.setdefault("action_gate", ActionGate())
        deliberation = context.config.get("deliberation_result")
        drives: DriveField | None = context.config.get("drives")
        state = context.state_store.state
        h = state.homeostatic
        focus = state.attention_focus
        wm = {k: v for k, v in state.working_memory_items}
        tick = context.clock.tick
        t = context.clock.simulation_time

        candidates = world.available_actions()
        persona_mods = context.config.get("persona_modifiers") or {}
        goal_rel = context.config.get("goal_relevance") or {}
        salience = context.config.get("action_salience") or {}
        base_scores: dict[str, float] = {}
        for action in candidates:
            info = world.action_info(action)
            score = float(info.get("base_value", 0.0))
            score -= float(info.get("cost_energy", 0.0)) * (1.0 - h.energy)
            risk = float(info.get("risk", 0.0))
            score -= risk * h.safety_need
            score -= risk * float(persona_mods.get("risk_aversion", 0.0))
            score += 0.18 * float(goal_rel.get(action, 0.0))
            distractibility = float(persona_mods.get("distractibility", 0.0))
            if distractibility > 0.0:
                sal = float(salience.get(action, info.get("salience", 0.0) or 0.0))
                rel = float(goal_rel.get(action, 0.0))
                if sal > 0.5 and rel < 0.3:
                    score += 0.2 * distractibility * sal
            exploration = float(persona_mods.get("exploration_tendency", 0.0))
            if exploration > 0.0:
                modality = str(info.get("modality") or info.get("affordance") or "")
                if modality in ("navigable", "inspectable", "scrollable") or "scroll" in action or "navigate" in action:
                    score += 0.12 * exploration
            if info.get("modality") in focus:
                score += 0.15
            if action in wm:
                score += 0.1 * wm[action]
            if drives is not None:
                score += drives.action_bias(action)
            base_scores[action] = score

        sleep_active = context.config.get("sleep_active")
        sleep_phase = context.config.get("sleep_phase", "awake")
        if sleep_active and sleep_phase in ("nrem_deep", "rem", "nrem_light"):
            for action in list(base_scores):
                if action == "rest":
                    base_scores[action] += 0.5
                else:
                    base_scores[action] -= 0.35

        for action_key, bias in (context.config.get("workspace_action_bias") or {}).items():
            if action_key in base_scores:
                base_scores[action_key] += bias
        for action_key, bias in (context.config.get("social_action_bias") or {}).items():
            if action_key in base_scores:
                base_scores[action_key] += bias

        retrieved_boost: dict[str, float] = {}
        episodic_gain = route_gain(
            context.router,
            "hippocampus",
            "prefrontal",
            (0.7, 0.3, 0.2),
        )
        for ep, sim in context.config.get("retrieved_episodes") or []:
            if ep.action:
                retrieved_boost[ep.action] = (
                    retrieved_boost.get(ep.action, 0.0) + 0.12 * sim * ep.confidence * episodic_gain
                )

        executive_gain = 1.0
        if deliberation is not None:
            choice_idx = max(0, candidates.index(deliberation.choice_key)) if deliberation.choice_key in candidates else 0
            executive_gain = route_gain(
                context.router,
                "prefrontal",
                "basal_ganglia",
                (deliberation.confidence, float(choice_idx) * 0.1, deliberation.conflict),
            )
        context.config["connectome_executive_gain"] = executive_gain
        context.config["connectome_episodic_gain"] = episodic_gain

        best, confidence, scores, vetoed = gate.select(
            candidates=candidates,
            base_scores=base_scores,
            deliberation=deliberation,
            retrieved_boost=retrieved_boost,
            td_biases=context.config.get("td_go_biases"),
            rng=context.rng,
            executive_gain=executive_gain,
        )

        events: list[CognitiveEvent] = [
            CognitiveEvent(
                event_type="action.selected",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "action": best,
                    "confidence": confidence,
                    "candidates": tuple(candidates),
                    "scores": {k: round(v, 4) for k, v in scores.items()},
                    "integrated_bg": True,
                },
            )
        ]
        if vetoed:
            events.append(
                CognitiveEvent(
                    event_type="action.vetoed",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={"pfc_veto": True, "selected": best},
                )
            )
        return events


@dataclass
class CerebellarCorrectionProcess(BaseProcess):
    """Suavizado cerebelar antes de ejecución motora."""

    process_id: str = "cerebellar_correction"
    period_ticks: int = 1
    priority: int = 56

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        action = context.state_store.state.current_action
        if not action:
            return []
        coordinator: CerebellarCoordinator = context.config.setdefault(
            "cerebellum", CerebellarCoordinator()
        )
        tick = context.clock.tick
        t = context.clock.simulation_time
        confidence = context.state_store.state.confidence
        corrected, new_conf = coordinator.correct(action, confidence=confidence)
        if corrected == action:
            context.config["motor_action"] = action
            return []

        context.config["motor_action"] = corrected
        return [
            CognitiveEvent(
                event_type="action.corrected",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "action": corrected,
                    "original": action,
                    "confidence": new_conf,
                },
            )
        ]
