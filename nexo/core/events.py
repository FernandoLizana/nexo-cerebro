"""Eventos cognitivos inmutables con trazabilidad causal."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


def new_trace_id() -> str:
    return uuid4().hex[:16]


@dataclass(frozen=True)
class CognitiveEvent:
    """Evento base; todos los campos de trazabilidad son obligatorios."""

    event_type: str
    source: str
    tick: int
    simulation_time: float
    payload: dict[str, Any] = field(default_factory=dict)
    target: str | None = None
    causal_parent: str | None = None
    trace_id: str = field(default_factory=new_trace_id)

    def child(self, event_type: str, source: str, payload: dict[str, Any] | None = None) -> CognitiveEvent:
        return CognitiveEvent(
            event_type=event_type,
            source=source,
            tick=self.tick,
            simulation_time=self.simulation_time,
            payload=dict(payload or {}),
            target=self.target,
            causal_parent=self.trace_id,
        )


@dataclass(frozen=True)
class HomeostaticEnergyChanged(CognitiveEvent):
    def __init__(self, *, source: str, delta: float, tick: int, simulation_time: float, trace_id: str | None = None):
        object.__setattr__(
            self,
            "__dict__",
            CognitiveEvent(
                event_type="homeostatic.energy_changed",
                source=source,
                tick=tick,
                simulation_time=simulation_time,
                payload={"delta": float(delta)},
                trace_id=trace_id or new_trace_id(),
            ).__dict__,
        )


@dataclass(frozen=True)
class PerceptionUpdated(CognitiveEvent):
    def __init__(
        self,
        *,
        source: str,
        modality: str,
        embedding: tuple[float, ...],
        salience: float,
        tick: int,
        simulation_time: float,
    ):
        object.__setattr__(
            self,
            "__dict__",
            CognitiveEvent(
                event_type="perception.updated",
                source=source,
                tick=tick,
                simulation_time=simulation_time,
                payload={
                    "modality": modality,
                    "embedding": embedding,
                    "salience": float(salience),
                },
            ).__dict__,
        )


@dataclass(frozen=True)
class AttentionFocusChanged(CognitiveEvent):
    def __init__(self, *, source: str, focus: tuple[str, ...], tick: int, simulation_time: float):
        object.__setattr__(
            self,
            "__dict__",
            CognitiveEvent(
                event_type="attention.focus_changed",
                source=source,
                tick=tick,
                simulation_time=simulation_time,
                payload={"focus": focus},
            ).__dict__,
        )


@dataclass(frozen=True)
class ActionSelected(CognitiveEvent):
    def __init__(
        self,
        *,
        source: str,
        action: str,
        confidence: float,
        candidates: tuple[str, ...],
        tick: int,
        simulation_time: float,
    ):
        object.__setattr__(
            self,
            "__dict__",
            CognitiveEvent(
                event_type="action.selected",
                source=source,
                tick=tick,
                simulation_time=simulation_time,
                payload={
                    "action": action,
                    "confidence": float(confidence),
                    "candidates": candidates,
                },
            ).__dict__,
        )


@dataclass(frozen=True)
class MemoryEncoded(CognitiveEvent):
    def __init__(self, *, source: str, episode_id: str, tick: int, simulation_time: float):
        object.__setattr__(
            self,
            "__dict__",
            CognitiveEvent(
                event_type="memory.encoded",
                source=source,
                tick=tick,
                simulation_time=simulation_time,
                payload={"episode_id": episode_id},
            ).__dict__,
        )
