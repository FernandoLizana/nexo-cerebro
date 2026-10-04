"""Cognitive Persona models — traits vs state, serializable."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class PersonaTraits:
    """Immutable trait profile — ENGINEERING DEFAULT, NOT HUMAN-CALIBRATED."""

    working_memory_capacity: int = 4
    attention_persistence: float = 0.5
    distractibility: float = 0.5
    visual_search_efficiency: float = 0.5
    risk_aversion: float = 0.5
    patience: float = 0.5
    frustration_tolerance: float = 0.5
    exploration_tendency: float = 0.5
    digital_literacy: float = 0.5
    semantic_confidence: float = 0.5
    initial_fatigue: float = 0.0
    impulsivity: float = 0.5
    learning_rate_modifier: float = 1.0
    metacognitive_sensitivity: float = 0.5
    fatigue_rate_modifier: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_mapping(cls, data: dict | None) -> PersonaTraits:
        data = dict(data or {})
        kwargs = {}
        for key in cls.__dataclass_fields__:
            if key not in data:
                continue
            val = data[key]
            if key == "working_memory_capacity":
                kwargs[key] = int(val)
            elif key == "learning_rate_modifier":
                kwargs[key] = float(val)
            else:
                kwargs[key] = float(val)
        return cls(**kwargs)


@dataclass
class PersonaState:
    """Dynamic cognitive state during a run — traits remain fixed."""

    current_frustration: float = 0.0
    current_fatigue: float = 0.0
    current_confidence: float = 0.5
    ticks_without_progress: int = 0
    repeated_action_count: int = 0
    last_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_frustration": self.current_frustration,
            "current_fatigue": self.current_fatigue,
            "current_confidence": self.current_confidence,
            "ticks_without_progress": self.ticks_without_progress,
            "repeated_action_count": self.repeated_action_count,
            "last_action": self.last_action,
        }


@dataclass(frozen=True, slots=True)
class CognitivePersona:
    persona_id: str
    schema_version: int
    traits: PersonaTraits
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def config_hash(self) -> str:
        blob = json.dumps(self.traits.to_dict(), sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "schema_version": self.schema_version,
            "config_hash": self.config_hash(),
            "description": self.description,
            "traits": self.traits.to_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class MechanisticMappingEntry:
    trait_field: str
    module: str
    parameter: str
    effect: str


@dataclass
class PersonaApplicationReport:
    persona_id: str
    config_hash: str
    mappings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "config_hash": self.config_hash,
            "mappings": list(self.mappings),
        }

    def add(self, *, trait: str, module: str, parameter: str, requested: Any, effective: Any, effect: str) -> None:
        self.mappings.append(
            {
                "trait": trait,
                "module": module,
                "parameter": parameter,
                "requested": requested,
                "effective": effective,
                "effect": effect,
            }
        )
