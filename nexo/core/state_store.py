"""Reducer de estado mediante eventos tipados."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from nexo.core.cognitive_state import AffectiveState, CognitiveState, HomeostaticState
from nexo.core.events import CognitiveEvent


def reduce_state(state: CognitiveState, event: CognitiveEvent) -> CognitiveState:
    et = event.event_type
    p = event.payload

    if et == "homeostatic.energy_changed":
        h = state.homeostatic
        return state.with_homeostatic(replace(h, energy=h.energy + float(p.get("delta", 0.0))))

    if et == "homeostatic.hydration_changed":
        h = state.homeostatic
        return state.with_homeostatic(replace(h, hydration=h.hydration + float(p.get("delta", 0.0))))

    if et == "homeostatic.pain_changed":
        h = state.homeostatic
        return state.with_homeostatic(replace(h, pain=h.pain + float(p.get("delta", 0.0))))

    if et == "homeostatic.fatigue_changed":
        h = state.homeostatic
        return state.with_homeostatic(replace(h, fatigue=h.fatigue + float(p.get("delta", 0.0))))

    if et == "homeostatic.sleep_pressure_changed":
        h = state.homeostatic
        return state.with_homeostatic(replace(h, sleep_pressure=h.sleep_pressure + float(p.get("delta", 0.0))))

    if et == "homeostatic.stress_load_changed":
        h = state.homeostatic
        return state.with_homeostatic(replace(h, stress_load=h.stress_load + float(p.get("delta", 0.0))))

    if et == "homeostatic.social_need_changed":
        h = state.homeostatic
        return state.with_homeostatic(replace(h, social_need=h.social_need + float(p.get("delta", 0.0))))

    if et == "homeostatic.safety_need_changed":
        h = state.homeostatic
        return state.with_homeostatic(replace(h, safety_need=h.safety_need + float(p.get("delta", 0.0))))

    if et == "affect.updated":
        a = state.affective
        return state.with_affective(
            AffectiveState(
                valence=float(p.get("valence", a.valence)),
                arousal=float(p.get("arousal", a.arousal)),
                dominance=float(p.get("dominance", a.dominance)),
                uncertainty=float(p.get("uncertainty", a.uncertainty)),
                threat=float(p.get("threat", a.threat)),
                frustration=float(p.get("frustration", a.frustration)),
                curiosity=float(p.get("curiosity", a.curiosity)),
                mood_baseline=float(p.get("mood_baseline", a.mood_baseline)),
            )
        )

    if et == "attention.focus_changed":
        return replace(state, attention_focus=tuple(p.get("focus", ())))

    if et == "working_memory.updated":
        items = tuple((str(k), float(v)) for k, v in p.get("items", []))
        return replace(state, working_memory_items=items)

    if et == "workspace.broadcast":
        content = tuple(str(x) for x in p.get("content", ()))
        return replace(state, global_workspace_content=content)

    if et == "action.selected":
        return replace(
            state,
            current_action=str(p.get("action")),
            confidence=float(p.get("confidence", state.confidence)),
        )

    if et == "action.unified":
        return replace(
            state,
            current_action=str(p.get("action")),
            confidence=float(p.get("confidence", state.confidence)),
        )

    if et == "action.weighted":
        return replace(
            state,
            current_action=str(p.get("action")),
            confidence=float(p.get("confidence", state.confidence)),
        )

    if et == "action.corrected":
        return replace(
            state,
            current_action=str(p.get("action")),
            confidence=float(p.get("confidence", state.confidence)),
        )

    if et == "reward.received":
        return replace(state, last_reward=float(p.get("value", 0.0)))

    if et == "goals.updated":
        return replace(state, active_goals=tuple(str(g) for g in p.get("goals", state.active_goals)))

    if et == "plan.updated":
        return state

    if et == "deliberation.completed":
        return state

    if et == "metacognition.updated":
        return state

    if et in ("social.perceived", "social.tom_inferred", "social.exchange", "language.produced"):
        return state

    if et in ("sleep.phase_changed", "memory.replayed", "memory.consolidated", "development.updated"):
        return state

    if et == "behavior.snapshot":
        return state

    if et == "behavior.fingerprint":
        return state

    if et == "connectome.lesion_applied":
        return state

    if et == "connectome.signal_delivered":
        return state

    if et == "connectome.routing_active":
        return state

    if et == "telemetry.trace":
        return state

    if et == "perception.prediction_error":
        digest = state.trajectory_digest + (float(p.get("surprise", 0.0)),)
        return replace(state, trajectory_digest=digest[-32:])

    if et == "thalamus.relayed":
        return state

    if et == "memory.retrieved":
        digest = state.trajectory_digest + (float(p.get("similarity", 0.0)),)
        return replace(state, trajectory_digest=digest[-32:])

    return state


@dataclass
class StateStore:
    """Almacén inmutable con historial de eventos."""

    state: CognitiveState = field(default_factory=CognitiveState)
    event_log: list[CognitiveEvent] = field(default_factory=list)
    max_log: int = 5000

    def dispatch(self, event: CognitiveEvent) -> CognitiveState:
        self.state = reduce_state(self.state, event)
        self.event_log.append(event)
        if len(self.event_log) > self.max_log:
            self.event_log = self.event_log[-self.max_log :]
        return self.state

    def dispatch_many(self, events: list[CognitiveEvent]) -> CognitiveState:
        for ev in events:
            self.dispatch(ev)
        return self.state

    def snapshot(self) -> CognitiveState:
        return self.state
