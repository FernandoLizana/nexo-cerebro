"""Cognitive QA analysis models — events, observations, raw trace."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

SCHEMA_VERSION = 1


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class CognitiveQAEvent:
    """Normalized QA event — adapter over NEXO CognitiveEvent + world trace."""

    event_id: str
    trace_id: str
    run_id: str
    tick: int
    simulation_time: float
    event_type: str
    source: str
    goal_id: str | None = None
    persona_id: str | None = None
    scene_id: str | None = None
    percept_id: str | None = None
    action_id: str | None = None
    outcome_id: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "tick": self.tick,
            "simulation_time": self.simulation_time,
            "event_type": self.event_type,
            "source": self.source,
            "goal_id": self.goal_id,
            "persona_id": self.persona_id,
            "scene_id": self.scene_id,
            "percept_id": self.percept_id,
            "action_id": self.action_id,
            "outcome_id": self.outcome_id,
            "evidence": dict(self.evidence),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class CognitiveQAObservation:
    """Derived observation — not necessarily a failure."""

    observation_id: str
    category: str
    description: str
    start_tick: int
    end_tick: int
    severity_hint: str = "INFO"
    confidence: float = 0.5
    evidence_refs: tuple[str, ...] = ()
    persona_state_refs: dict[str, Any] = field(default_factory=dict)
    goal_state_refs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "category": self.category,
            "description": self.description,
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "severity_hint": self.severity_hint,
            "confidence": round(self.confidence, 4),
            "evidence_refs": list(self.evidence_refs),
            "persona_state_refs": dict(self.persona_state_refs),
            "goal_state_refs": dict(self.goal_state_refs),
        }


@dataclass
class RawRunTrace:
    """Immutable raw capture for offline P6 analysis."""

    run_id: str
    seed: int
    ticks: int
    events: list[dict[str, Any]]
    world_trace: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    def content_hash(self) -> str:
        blob = json.dumps(
            {"events": self.events, "world_trace": self.world_trace, "metadata": self.metadata},
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "seed": self.seed,
            "ticks": self.ticks,
            "content_hash": self.content_hash(),
            "events": self.events,
            "world_trace": self.world_trace,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RawRunTrace:
        return cls(
            run_id=str(data.get("run_id", _new_id("run"))),
            seed=int(data.get("seed", 0)),
            ticks=int(data.get("ticks", 0)),
            events=list(data.get("events") or []),
            world_trace=list(data.get("world_trace") or []),
            metadata=dict(data.get("metadata") or {}),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
        )
