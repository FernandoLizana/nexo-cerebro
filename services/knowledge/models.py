"""Graph node/edge records (backend-agnostic)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from services.knowledge.types import (
    ALLOWED_EDGE_RELATIONS,
    ALLOWED_NODE_KINDS,
    EdgeRelation,
    NodeKind,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_node_id(kind: NodeKind | str, suffix: str | None = None) -> str:
    kind_s = kind.value if isinstance(kind, NodeKind) else str(kind)
    tail = suffix or uuid.uuid4().hex[:12]
    return f"{kind_s.lower()}:{tail}"


def new_edge_id() -> str:
    return f"edge-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class GraphNode:
    node_id: str
    kind: NodeKind
    label: str = ""
    props: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "kind": self.kind.value,
            "label": self.label,
            "props": dict(self.props),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> GraphNode:
        kind_raw = str(data.get("kind") or "")
        if kind_raw not in ALLOWED_NODE_KINDS:
            raise ValueError(f"node kind not allowlisted: {kind_raw!r}")
        return cls(
            node_id=str(data.get("node_id") or new_node_id(kind_raw)),
            kind=NodeKind(kind_raw),
            label=str(data.get("label") or ""),
            props=dict(data.get("props") or {}),
            created_at=str(data.get("created_at") or _utc_now()),
        )


@dataclass(frozen=True, slots=True)
class GraphEdge:
    edge_id: str
    source_id: str
    target_id: str
    relation: EdgeRelation
    weight: float = 1.0
    confidence: float = 0.5
    props: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation.value,
            "weight": float(max(0.0, min(1.0, self.weight))),
            "confidence": float(max(0.0, min(1.0, self.confidence))),
            "props": dict(self.props),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> GraphEdge:
        rel_raw = str(data.get("relation") or "")
        if rel_raw not in ALLOWED_EDGE_RELATIONS:
            raise ValueError(f"edge relation not allowlisted: {rel_raw!r}")
        return cls(
            edge_id=str(data.get("edge_id") or new_edge_id()),
            source_id=str(data.get("source_id") or ""),
            target_id=str(data.get("target_id") or ""),
            relation=EdgeRelation(rel_raw),
            weight=float(data.get("weight") if data.get("weight") is not None else 1.0),
            confidence=float(
                data.get("confidence") if data.get("confidence") is not None else 0.5
            ),
            props=dict(data.get("props") or {}),
            created_at=str(data.get("created_at") or _utc_now()),
        )
