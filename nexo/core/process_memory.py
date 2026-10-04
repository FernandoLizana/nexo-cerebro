"""Procesos Sprint 4 — memoria de trabajo e hipocampo."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

import numpy as np

from nexo.core.events import CognitiveEvent
from nexo.core.module_protocol import ProcessContext
from nexo.core.process import BaseProcess
from nexo.interventions.routing_helpers import route_gain
from nexo.memory.hippocampus.episode import EpisodicMemory
from nexo.memory.hippocampus.store import HippocampalStore
from nexo.working_memory.buffer import WorkingMemoryBuffer


def _memory_rng(context: ProcessContext) -> np.random.Generator:
    return context.config.get("memory_rng") or context.rng


@dataclass
class EnhancedWorkingMemoryProcess(BaseProcess):
    """WM con decaimiento, interferencia y efectos de primacía/recencia."""

    process_id: str = "working_memory"
    period_ticks: int = 2
    priority: int = 65

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        tick = context.clock.tick
        t = context.clock.simulation_time
        buf: WorkingMemoryBuffer = context.config.setdefault(
            "wm_buffer", WorkingMemoryBuffer(capacity=4)
        )
        focus = context.state_store.state.attention_focus
        percepts = [
            ev.payload
            for ev in context.state_store.event_log[-25:]
            if ev.event_type == "perception.updated"
        ]
        for p in percepts:
            mod = str(p.get("modality", ""))
            if mod in focus:
                emb = tuple(p.get("posterior") or p.get("embedding") or ())
                buf.gate_in(mod, embedding=emb, tick=tick, priority=1.0 + float(p.get("salience", 0)))
        buf.tick_decay(tick)
        routing_mode = context.config.get("routing_mode", "legacy")
        wm_gain = 1.0
        items = buf.to_tuples()
        if routing_mode == "integrated" and items:
            signal = tuple(float(v) for _, v in items[:3])
            wm_gain = route_gain(context.router, "working_memory", "prefrontal", signal)
            context.config["connectome_wm_route_gain"] = wm_gain
        scaled_items = [(k, round(v * wm_gain, 5)) for k, v in items]
        return [
            CognitiveEvent(
                event_type="working_memory.updated",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "items": scaled_items,
                    "connectome_routed": routing_mode == "integrated",
                    "wm_route_gain": round(wm_gain, 5),
                },
            )
        ]


@dataclass
class HippocampalEncoderProcess(BaseProcess):
    """Codificación episódica rápida tras acciones salientes."""

    process_id: str = "hippocampal_encoder"
    period_ticks: int = 1
    priority: int = 52
    min_reward_to_encode: float = 0.08

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        store: HippocampalStore = context.config.setdefault("hippocampal_store", HippocampalStore())
        tick = context.clock.tick
        t = context.clock.simulation_time
        state = context.state_store.state
        events: list[CognitiveEvent] = []

        recent = context.state_store.event_log[-100:]
        action_ev = next(
            (e for e in reversed(recent) if e.event_type == "action.selected" and e.tick == tick),
            None,
        )
        if action_ev is None:
            action_ev = next((e for e in reversed(recent) if e.event_type == "action.selected"), None)
        reward_ev = next(
            (e for e in reversed(recent) if e.event_type == "reward.received" and e.tick == tick),
            None,
        )
        if reward_ev is None:
            reward_ev = next((e for e in reversed(recent) if e.event_type == "reward.received"), None)
        if action_ev is None:
            return []

        reward = float(reward_ev.payload.get("value", 0.0)) if reward_ev else 0.0
        if reward < self.min_reward_to_encode and action_ev.payload.get("action") not in ("eat", "flee"):
            return []

        hctrl = context.config.get("homeostatic_controller")
        body = hctrl.body.to_homeostatic_dict() if hctrl else {}
        affect = (
            state.affective.valence,
            state.affective.arousal,
            state.affective.threat,
        )
        percepts = [
            ev.payload for ev in recent if ev.event_type == "perception.updated"
        ]
        emb = (0.0, 0.0, 0.0)
        modality = ""
        if percepts:
            p = percepts[-1]
            modality = str(p.get("modality", ""))
            emb = tuple(p.get("posterior") or p.get("embedding") or (0.0, 0.0, 0.0))

        episode = EpisodicMemory(
            episode_id=uuid4().hex[:10],
            event_embedding=emb,
            spatial_context=(float(body.get("energy", 0.5)), float(reward)),
            temporal_context=(float(tick), float(t % 86400.0)),
            body_context=(
                float(body.get("energy", 0.5)),
                float(body.get("fatigue", 0.0)),
                float(body.get("pain", 0.0)),
            ),
            affective_context=affect,
            action=str(action_ev.payload.get("action")),
            outcome=f"reward={reward:.3f}",
            confidence=min(0.95, 0.4 + reward),
            source_identity="self",
            tick=tick,
            modality=modality,
        )
        encoded = store.encode(episode, rng=_memory_rng(context))
        if encoded is None:
            return []
        events.append(
            CognitiveEvent(
                event_type="memory.encoded",
                source=self.process_id,
                tick=tick,
                simulation_time=t,
                payload={
                    "episode_id": encoded.episode_id,
                    "action": encoded.action,
                    "modality": encoded.modality,
                    "confidence": encoded.confidence,
                },
            )
        )
        return events


@dataclass
class HippocampalRetrievalProcess(BaseProcess):
    """Recuperación asociativa con pattern completion."""

    process_id: str = "hippocampal_retrieval"
    period_ticks: int = 2
    priority: int = 62

    def step(self, context: ProcessContext) -> list[CognitiveEvent]:
        store: HippocampalStore | None = context.config.get("hippocampal_store")
        if store is None or not store.episodes:
            context.config["retrieved_episodes"] = []
            return []

        tick = context.clock.tick
        t = context.clock.simulation_time
        focus = context.state_store.state.attention_focus
        cue_parts: list[float] = []
        for mod in focus:
            for ev in reversed(context.state_store.event_log[-15:]):
                if ev.event_type == "perception.updated" and ev.payload.get("modality") == mod:
                    emb = ev.payload.get("posterior") or ev.payload.get("embedding") or ()
                    cue_parts.extend(float(x) for x in emb[:3])
                    break
        if not cue_parts:
            cue_parts = [0.1, float(tick) * 0.01]

        retrieved = store.retrieve_partial(tuple(cue_parts), rng=_memory_rng(context), top_k=2)
        routing_mode = context.config.get("routing_mode", "legacy")
        if routing_mode == "integrated":
            cue_vec = tuple(cue_parts[:3]) if cue_parts else (0.1, 0.1, 0.1)
            route_scale = route_gain(context.router, "hippocampus", "prefrontal", cue_vec)
            retrieved = [(ep, sim * route_scale) for ep, sim in retrieved]
            context.config["connectome_episodic_route_gain"] = route_scale
        context.config["retrieved_episodes"] = retrieved

        events: list[CognitiveEvent] = []
        for ep, sim in retrieved:
            events.append(
                CognitiveEvent(
                    event_type="memory.retrieved",
                    source=self.process_id,
                    tick=tick,
                    simulation_time=t,
                    payload={
                        "episode_id": ep.episode_id,
                        "action": ep.action,
                        "modality": ep.modality,
                        "similarity": sim,
                        "confidence": ep.confidence,
                        "reconstructed": True,
                        "connectome_routed": routing_mode == "integrated",
                    },
                )
            )
        return events
