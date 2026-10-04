"""Implementaciones concretas de procesos cognitivos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import CognitiveProcess, ProcessContext


@dataclass
class BaseProcess:
    process_id: str
    period_ticks: int = 1
    phase_offset: int = 0
    priority: int = 50
    enabled: bool = True

    def should_run(self, tick: int) -> bool:
        if not self.enabled:
            return False
        return (tick - self.phase_offset) % max(1, self.period_ticks) == 0


@dataclass
class SensoryRelayProcess(BaseProcess):
    """Percepción sensorial desde el mundo simulado."""

    process_id: str = "sensory_relay"
    period_ticks: int = 1
    priority: int = 90

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        world = context.config.get("world_state")
        if world is None:
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        events: list[CognitiveEvent] = []
        for modality, salience, vec in world.percepts_for_agent():
            routed = context.router.route("sensory_hub", f"{modality}_cortex", vec, salience)
            events.append(
                CognitiveEvent(
                    event_type="perception.updated",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={
                        "modality": modality,
                        "embedding": tuple(float(x) for x in routed),
                        "salience": float(salience),
                    },
                )
            )
        return events


@dataclass
class InteroceptionProcess(BaseProcess):
    """Deprecated alias — usar BodyInteroceptionProcess vía process_body."""

    process_id: str = "interoception_legacy"
    period_ticks: int = 999
    priority: int = 0

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        return []


@dataclass
class HomeostasisProcess(BaseProcess):
    """Deprecated — reemplazado por MetabolismProcess (Sprint 2)."""

    process_id: str = "homeostasis_legacy"
    period_ticks: int = 999
    priority: int = 0

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        return []


@dataclass
class AttentionProcess(BaseProcess):
    process_id: str = "attention"
    period_ticks: int = 2
    priority: int = 70

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        tick = context.clock.tick
        t = context.clock.simulation_time
        percepts = [
            ev.payload
            for ev in context.state_store.event_log[-20:]
            if ev.event_type == "perception.updated"
        ]
        if not percepts:
            return []
        scored: list[tuple[float, str]] = []
        goals = set(context.state_store.state.active_goals)
        for p in percepts:
            mod = str(p.get("modality", ""))
            sal = float(p.get("salience", 0.0))
            goal_bonus = 0.2 if mod == "food" and "eat" in goals else 0.0
            threat_bonus = 0.3 if mod == "danger" and ("survive" in goals or "avoid_harm" in goals) else 0.0
            scored.append((sal + goal_bonus + threat_bonus, mod))
        scored.sort(reverse=True)
        focus = tuple(m for _, m in scored[:2])
        return [
            CognitiveEvent(
                event_type="attention.focus_changed",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={"focus": focus},
            )
        ]


@dataclass
class WorkingMemoryProcess(BaseProcess):
    process_id: str = "working_memory"
    period_ticks: int = 2
    priority: int = 65
    capacity: int = 4

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        tick = context.clock.tick
        t = context.clock.simulation_time
        focus = context.state_store.state.attention_focus
        items = list(context.state_store.state.working_memory_items)
        for f in focus:
            if not any(k == f for k, _ in items):
                items.append((f, 1.0))
        items = [(k, max(0.0, v - 0.05)) for k, v in items if v > 0.05]
        items = items[-self.capacity :]
        return [
            CognitiveEvent(
                event_type="working_memory.updated",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={"items": items},
            )
        ]


@dataclass
class BasalGangliaSelectorProcess(BaseProcess):
    """Selección competitiva de acciones — drives homeostáticos + competencia."""

    process_id: str = "basal_ganglia_selector"
    period_ticks: int = 1
    priority: int = 60

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        world = context.config.get("world_state")
        if world is None:
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        state = context.state_store.state
        h = state.homeostatic
        focus = state.attention_focus
        wm = {k: v for k, v in state.working_memory_items}
        drives = context.config.get("drives")

        candidates = world.available_actions()
        scores: dict[str, float] = {}
        for action in candidates:
            info = world.action_info(action)
            score = float(info.get("base_value", 0.0))
            score -= float(info.get("cost_energy", 0.0)) * (1.0 - h.energy)
            score -= float(info.get("risk", 0.0)) * h.safety_need
            if info.get("modality") in focus:
                score += 0.15
            if action in wm:
                score += 0.1 * wm[action]
            if drives is not None:
                score += drives.action_bias(action)
            sleep_active = context.config.get("sleep_active")
            sleep_phase = context.config.get("sleep_phase", "awake")
            if sleep_active and sleep_phase in ("nrem_deep", "rem", "nrem_light"):
                if action == "rest":
                    score += 0.5
                else:
                    score -= 0.35
            for action_key, bias in (context.config.get("workspace_action_bias") or {}).items():
                if action_key == action:
                    score += bias
            for action_key, bias in (context.config.get("social_action_bias") or {}).items():
                if action_key == action:
                    score += bias
            retrieved = context.config.get("retrieved_episodes") or []
            for ep, sim in retrieved:
                if ep.action == action:
                    score += 0.12 * sim * ep.confidence
            for action_key, bias in (context.config.get("td_go_biases") or {}).items():
                if action_key == action:
                    score += bias
            scores[action] = score + context.rng.normal(0.0, 0.03)

        if not scores:
            return []
        best = max(scores, key=scores.get)
        margin = scores[best] - sorted(scores.values())[-2] if len(scores) > 1 else scores[best]
        confidence = float(max(0.1, min(0.99, 0.5 + margin * 0.3)))
        return [
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
                },
            )
        ]


@dataclass
class MotorExecutionProcess(BaseProcess):
    process_id: str = "motor_execution"
    period_ticks: int = 1
    priority: int = 55

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        world = context.config.get("world_state")
        action = context.config.get("motor_action") or context.state_store.state.current_action
        if world is None or not action:
            return []
        tick = context.clock.tick
        t = context.clock.simulation_time
        hctrl = context.config.get("homeostatic_controller")
        outcome = world.apply_action(action)
        context.config.pop("motor_action", None)
        events: list[CognitiveEvent] = [
            CognitiveEvent(
                event_type="reward.received",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={"value": float(outcome.get("reward", 0.0))},
            )
        ]
        if hctrl is not None:
            body_deltas = hctrl.metabolism.apply_action(hctrl.body, action)
            for key, delta in body_deltas.items():
                if key == "action":
                    continue
                et = f"homeostatic.{key}_changed"
                events.append(
                    CognitiveEvent(
                        event_type=et,
                        source=self.process_id,
                        tick=tick,
                        simulation_time=t,
                        payload={"delta": float(delta)},
                    )
                )
            if hasattr(world, "sync_from_body"):
                world.sync_from_body(hctrl.body)
        else:
            for key, delta in outcome.get("homeostatic_deltas", {}).items():
                events.append(
                    CognitiveEvent(
                        event_type=f"homeostatic.{key}_changed",
                        source=self.process_id,
                        tick=tick,
                        simulation_time=t,
                        payload={"delta": float(delta)},
                    )
                )
        if outcome.get("encoded_memory"):
            events.append(
                CognitiveEvent(
                    event_type="memory.world_episode",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={"episode_id": str(outcome["encoded_memory"])},
                )
            )
        return events


@dataclass
class EpisodicMemoryProcess(BaseProcess):
    process_id: str = "episodic_memory"
    period_ticks: int = 5
    priority: int = 50
    _episodes: list[dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        if self._episodes is None:
            self._episodes = []

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        return []


@dataclass
class LegacyBrainAdapterProcess(BaseProcess):
    """Puente opcional al InfantApeBrain legacy (un paso headless por ciclo)."""

    process_id: str = "legacy_brain_adapter"
    period_ticks: int = 5
    priority: int = 40

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
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
                    },
                )
            )
        return events
