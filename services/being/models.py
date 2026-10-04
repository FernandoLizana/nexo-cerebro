"""Being domain models — split IDENTITY / MEMORY / STATE / COGNITIVE CONFIG."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


BEING_FORMAT_VERSION = "being-v1"

EXPERIMENTAL_DISCLAIMER = (
    "These personality and drive parameters are experimental controls for "
    "synthetic agents. They do not represent validated human psychology, "
    "emotions, or consciousness."
)


class ExperimentalDisclaimer:
    text = EXPERIMENTAL_DISCLAIMER


class BeingSpecies(str, Enum):
    HUMANOID = "HUMANOID"
    ANIMAL = "ANIMAL"
    CREATURE = "CREATURE"
    EXPERIMENTAL = "EXPERIMENTAL"


class BeingArchetype(str, Enum):
    CUSTOM = "CUSTOM"
    DOG = "DOG"
    CAT = "CAT"
    CROW = "CROW"
    FOX = "FOX"
    ROBOT = "ROBOT"
    SLIME = "SLIME"
    RESEARCHER = "RESEARCHER"
    EXPLORER = "EXPLORER"


# Experimental slider keys (0.0–1.0). Not clinical constructs.
PERSONALITY_TRAITS: tuple[str, ...] = (
    "curiosity",
    "sociability",
    "impulsivity",
    "patience",
    "exploration",
    "caution",
    "cooperation",
    "competitiveness",
    "persistence",
    "trust",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_being_id() -> str:
    return f"being-{uuid.uuid4().hex[:16]}"


@dataclass
class CorePersonality:
    """Bounded experimental trait vector (CORE PERSONALITY)."""

    traits: dict[str, float] = field(default_factory=dict)
    interests: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    simulated_fears: list[str] = field(default_factory=list)
    preferences: list[str] = field(default_factory=list)
    communication_style: str = "neutral"
    disclaimer: str = EXPERIMENTAL_DISCLAIMER

    def normalized(self) -> CorePersonality:
        traits = {k: float(self.traits.get(k, 0.5)) for k in PERSONALITY_TRAITS}
        for key, value in list(traits.items()):
            traits[key] = max(0.0, min(1.0, value))
        return CorePersonality(
            traits=traits,
            interests=list(self.interests),
            goals=list(self.goals),
            simulated_fears=list(self.simulated_fears),
            preferences=list(self.preferences),
            communication_style=str(self.communication_style or "neutral"),
            disclaimer=EXPERIMENTAL_DISCLAIMER,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self.normalized())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> CorePersonality:
        data = dict(data or {})
        traits = dict(data.get("traits") or {})
        return cls(
            traits=traits,
            interests=list(data.get("interests") or []),
            goals=list(data.get("goals") or []),
            simulated_fears=list(data.get("simulated_fears") or []),
            preferences=list(data.get("preferences") or []),
            communication_style=str(data.get("communication_style") or "neutral"),
            disclaimer=EXPERIMENTAL_DISCLAIMER,
        ).normalized()

    @classmethod
    def defaults_for(cls, species: BeingSpecies, archetype: BeingArchetype) -> CorePersonality:
        base = {k: 0.5 for k in PERSONALITY_TRAITS}
        presets: dict[BeingArchetype, dict[str, float]] = {
            BeingArchetype.DOG: {
                "curiosity": 0.7,
                "sociability": 0.85,
                "trust": 0.8,
                "cooperation": 0.75,
                "exploration": 0.65,
            },
            BeingArchetype.CAT: {
                "curiosity": 0.75,
                "sociability": 0.35,
                "caution": 0.7,
                "independence": 0.0,  # ignored if unknown
                "exploration": 0.6,
                "impulsivity": 0.45,
            },
            BeingArchetype.CROW: {
                "curiosity": 0.9,
                "exploration": 0.85,
                "caution": 0.55,
                "competitiveness": 0.4,
            },
            BeingArchetype.FOX: {
                "curiosity": 0.8,
                "caution": 0.65,
                "exploration": 0.75,
                "impulsivity": 0.4,
            },
            BeingArchetype.ROBOT: {
                "patience": 0.8,
                "persistence": 0.85,
                "impulsivity": 0.15,
                "cooperation": 0.6,
            },
            BeingArchetype.SLIME: {
                "curiosity": 0.55,
                "exploration": 0.5,
                "sociability": 0.2,
                "caution": 0.3,
            },
            BeingArchetype.RESEARCHER: {
                "curiosity": 0.9,
                "patience": 0.75,
                "persistence": 0.8,
                "cooperation": 0.65,
            },
            BeingArchetype.EXPLORER: {
                "exploration": 0.9,
                "curiosity": 0.85,
                "caution": 0.35,
                "impulsivity": 0.55,
            },
        }
        base.update({k: v for k, v in presets.get(archetype, {}).items() if k in PERSONALITY_TRAITS})
        if species is BeingSpecies.ANIMAL:
            base["sociability"] = max(base["sociability"], 0.4)
        return cls(traits=base).normalized()


@dataclass
class BeingIdentity:
    being_id: str
    name: str
    species: BeingSpecies
    archetype: BeingArchetype
    creator_node: str
    created_at: str
    format_version: str = BEING_FORMAT_VERSION
    age_ticks: int = 0
    core_personality: CorePersonality = field(default_factory=CorePersonality)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "being_id": self.being_id,
            "name": self.name,
            "species": self.species.value,
            "archetype": self.archetype.value,
            "creator_node": self.creator_node,
            "created_at": self.created_at,
            "age_ticks": int(self.age_ticks),
            "core_personality": self.core_personality.to_dict(),
            "disclaimer": EXPERIMENTAL_DISCLAIMER,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BeingIdentity:
        return cls(
            being_id=str(data["being_id"]),
            name=str(data["name"]),
            species=BeingSpecies(str(data["species"])),
            archetype=BeingArchetype(str(data.get("archetype") or BeingArchetype.CUSTOM.value)),
            creator_node=str(data.get("creator_node") or "unknown-node"),
            created_at=str(data.get("created_at") or _utc_now()),
            format_version=str(data.get("format_version") or BEING_FORMAT_VERSION),
            age_ticks=int(data.get("age_ticks") or 0),
            core_personality=CorePersonality.from_dict(data.get("core_personality")),
        )


@dataclass
class TemporaryState:
    """TEMPORARY STATE — volatile drives / affect / WM (not core personality)."""

    drives: dict[str, float] = field(default_factory=dict)
    affect: dict[str, float] = field(default_factory=dict)
    working_memory: list[str] = field(default_factory=list)
    learned_behavior_notes: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": BEING_FORMAT_VERSION,
            "drives": {k: float(max(0.0, min(1.0, float(v)))) for k, v in self.drives.items()},
            "affect": {k: float(max(0.0, min(1.0, float(v)))) for k, v in self.affect.items()},
            "working_memory": list(self.working_memory)[:32],
            "learned_behavior_notes": list(self.learned_behavior_notes)[:64],
            "updated_at": self.updated_at,
            "layer": "TEMPORARY_STATE",
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> TemporaryState:
        data = dict(data or {})
        return cls(
            drives={str(k): float(v) for k, v in dict(data.get("drives") or {}).items()},
            affect={str(k): float(v) for k, v in dict(data.get("affect") or {}).items()},
            working_memory=[str(x) for x in list(data.get("working_memory") or [])],
            learned_behavior_notes=[str(x) for x in list(data.get("learned_behavior_notes") or [])],
            updated_at=str(data.get("updated_at") or _utc_now()),
        )

    @classmethod
    def defaults_for(cls, species: BeingSpecies) -> TemporaryState:
        if species is BeingSpecies.ANIMAL:
            drives = {
                "hunger": 0.3,
                "curiosity": 0.5,
                "energy": 0.7,
                "fear": 0.2,
                "affinity": 0.4,
                "territoriality": 0.3,
                "sociability": 0.5,
                "exploration": 0.5,
            }
        else:
            drives = {
                "curiosity": 0.5,
                "energy": 0.7,
                "social": 0.4,
                "safety": 0.2,
            }
        return cls(drives=drives, affect={"valence": 0.5, "arousal": 0.4})


@dataclass
class CognitiveConfiguration:
    """COGNITIVE CONFIGURATION — budgets and experimental knobs."""

    cognitive_budget: float = 1.0
    memory_level: str = "standard"  # minimal | standard | rich
    model_configuration: dict[str, Any] = field(default_factory=dict)
    behavioral_parameters: dict[str, float] = field(default_factory=dict)
    use_llm: bool = False
    disclaimer: str = EXPERIMENTAL_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        budget = max(0.05, min(1.0, float(self.cognitive_budget)))
        level = self.memory_level if self.memory_level in {"minimal", "standard", "rich"} else "standard"
        return {
            "format_version": BEING_FORMAT_VERSION,
            "cognitive_budget": budget,
            "memory_level": level,
            "model_configuration": dict(self.model_configuration),
            "behavioral_parameters": {
                str(k): float(max(0.0, min(1.0, float(v))))
                for k, v in self.behavioral_parameters.items()
            },
            "use_llm": bool(self.use_llm),
            "disclaimer": EXPERIMENTAL_DISCLAIMER,
            "layer": "COGNITIVE_CONFIGURATION",
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> CognitiveConfiguration:
        data = dict(data or {})
        return cls(
            cognitive_budget=float(data.get("cognitive_budget") or 1.0),
            memory_level=str(data.get("memory_level") or "standard"),
            model_configuration=dict(data.get("model_configuration") or {}),
            behavioral_parameters={
                str(k): float(v) for k, v in dict(data.get("behavioral_parameters") or {}).items()
            },
            use_llm=bool(data.get("use_llm", False)),
        )


@dataclass
class MemoryRecord:
    record_id: str
    content: str
    importance: float = 0.5
    confidence: float = 0.5
    timestamp: str = field(default_factory=_utc_now)
    source: str = "local"
    decay: float = 0.0
    recall_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "content": self.content,
            "importance": float(max(0.0, min(1.0, self.importance))),
            "confidence": float(max(0.0, min(1.0, self.confidence))),
            "timestamp": self.timestamp,
            "source": self.source,
            "decay": float(max(0.0, min(1.0, self.decay))),
            "recall_count": int(self.recall_count),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MemoryRecord:
        return cls(
            record_id=str(data.get("record_id") or uuid.uuid4().hex[:12]),
            content=str(data.get("content") or ""),
            importance=float(data.get("importance") or 0.5),
            confidence=float(data.get("confidence") or 0.5),
            timestamp=str(data.get("timestamp") or _utc_now()),
            source=str(data.get("source") or "local"),
            decay=float(data.get("decay") or 0.0),
            recall_count=int(data.get("recall_count") or 0),
        )


@dataclass
class MemoryBundle:
    """MEMORY layer — separate from identity to avoid giant identity files."""

    episodic: list[MemoryRecord] = field(default_factory=list)
    semantic: list[MemoryRecord] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    summaries: list[MemoryRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": BEING_FORMAT_VERSION,
            "layer": "MEMORY",
            "episodic": [r.to_dict() for r in self.episodic],
            "semantic": [r.to_dict() for r in self.semantic],
            "relationships": list(self.relationships),
            "summaries": [r.to_dict() for r in self.summaries],
            "disclaimer": EXPERIMENTAL_DISCLAIMER,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> MemoryBundle:
        data = dict(data or {})
        return cls(
            episodic=[MemoryRecord.from_dict(x) for x in list(data.get("episodic") or [])],
            semantic=[MemoryRecord.from_dict(x) for x in list(data.get("semantic") or [])],
            relationships=[dict(x) for x in list(data.get("relationships") or [])],
            summaries=[MemoryRecord.from_dict(x) for x in list(data.get("summaries") or [])],
        )


@dataclass
class Being:
    """In-memory aggregate; on disk parts stay split."""

    identity: BeingIdentity
    memory: MemoryBundle = field(default_factory=MemoryBundle)
    state: TemporaryState = field(default_factory=TemporaryState)
    cognitive: CognitiveConfiguration = field(default_factory=CognitiveConfiguration)
