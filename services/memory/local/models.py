"""Local memory record models (S8).

Compatible shape with ``services.being.models.MemoryRecord`` plus relationship peers.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


LOCAL_MEMORY_FORMAT = "local-memory-v1"


class MemoryKind(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    RELATIONSHIP = "relationship"
    SUMMARY = "summary"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_record_id(prefix: str = "mem") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


@dataclass
class LocalMemoryEntry:
    """Episodic / semantic / summary unit with decay + recall metadata."""

    record_id: str
    kind: MemoryKind
    content: str
    importance: float = 0.5
    confidence: float = 0.5
    timestamp: str = field(default_factory=_utc_now)
    source: str = "local"
    decay: float = 0.0
    recall_count: int = 0
    tags: list[str] = field(default_factory=list)

    def effective_score(self) -> float:
        """Retrieval priority — decays reduce score; never used as LLM dump key."""
        imp = max(0.0, min(1.0, float(self.importance)))
        conf = max(0.0, min(1.0, float(self.confidence)))
        dec = max(0.0, min(1.0, float(self.decay)))
        return imp * conf * (1.0 - dec)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "kind": self.kind.value,
            "content": self.content,
            "importance": float(max(0.0, min(1.0, self.importance))),
            "confidence": float(max(0.0, min(1.0, self.confidence))),
            "timestamp": self.timestamp,
            "source": self.source,
            "decay": float(max(0.0, min(1.0, self.decay))),
            "recall_count": int(self.recall_count),
            "tags": [str(t) for t in self.tags][:32],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> LocalMemoryEntry:
        kind_raw = str(data.get("kind") or MemoryKind.EPISODIC.value).lower()
        try:
            kind = MemoryKind(kind_raw)
        except ValueError:
            kind = MemoryKind.EPISODIC
        return cls(
            record_id=str(data.get("record_id") or new_record_id()),
            kind=kind,
            content=str(data.get("content") or ""),
            importance=float(data.get("importance") if data.get("importance") is not None else 0.5),
            confidence=float(data.get("confidence") if data.get("confidence") is not None else 0.5),
            timestamp=str(data.get("timestamp") or _utc_now()),
            source=str(data.get("source") or "local"),
            decay=float(data.get("decay") if data.get("decay") is not None else 0.0),
            recall_count=int(data.get("recall_count") or 0),
            tags=[str(t) for t in list(data.get("tags") or [])][:32],
        )


@dataclass
class RelationshipEntry:
    """Directed social / interaction memory toward another Being id."""

    record_id: str
    peer_being_id: str
    relation_type: str = "known"
    strength: float = 0.5
    notes: str = ""
    importance: float = 0.5
    confidence: float = 0.5
    timestamp: str = field(default_factory=_utc_now)
    source: str = "local"
    decay: float = 0.0
    recall_count: int = 0

    @property
    def kind(self) -> MemoryKind:
        return MemoryKind.RELATIONSHIP

    def content(self) -> str:
        return f"{self.relation_type}:{self.peer_being_id} {self.notes}".strip()

    def effective_score(self) -> float:
        imp = max(0.0, min(1.0, float(self.importance)))
        conf = max(0.0, min(1.0, float(self.confidence)))
        strength = max(0.0, min(1.0, float(self.strength)))
        dec = max(0.0, min(1.0, float(self.decay)))
        return imp * conf * strength * (1.0 - dec)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "kind": MemoryKind.RELATIONSHIP.value,
            "peer_being_id": self.peer_being_id,
            "relation_type": self.relation_type,
            "strength": float(max(0.0, min(1.0, self.strength))),
            "notes": self.notes,
            "importance": float(max(0.0, min(1.0, self.importance))),
            "confidence": float(max(0.0, min(1.0, self.confidence))),
            "timestamp": self.timestamp,
            "source": self.source,
            "decay": float(max(0.0, min(1.0, self.decay))),
            "recall_count": int(self.recall_count),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RelationshipEntry:
        return cls(
            record_id=str(data.get("record_id") or new_record_id("rel")),
            peer_being_id=str(data.get("peer_being_id") or ""),
            relation_type=str(data.get("relation_type") or "known"),
            strength=float(data.get("strength") if data.get("strength") is not None else 0.5),
            notes=str(data.get("notes") or ""),
            importance=float(data.get("importance") if data.get("importance") is not None else 0.5),
            confidence=float(data.get("confidence") if data.get("confidence") is not None else 0.5),
            timestamp=str(data.get("timestamp") or _utc_now()),
            source=str(data.get("source") or "local"),
            decay=float(data.get("decay") if data.get("decay") is not None else 0.0),
            recall_count=int(data.get("recall_count") or 0),
        )
