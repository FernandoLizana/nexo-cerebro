"""KnowledgeGraph protocol — backends must satisfy this contract (no Neo4j lock-in)."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from services.knowledge.models import GraphEdge, GraphNode
from services.knowledge.types import EdgeRelation, NodeKind


@runtime_checkable
class KnowledgeGraph(Protocol):
    """Abstract knowledge graph surface for Swarm services."""

    def upsert_node(
        self,
        *,
        kind: NodeKind | str,
        node_id: str | None = None,
        label: str = "",
        props: dict | None = None,
    ) -> GraphNode: ...

    def get_node(self, node_id: str) -> GraphNode | None: ...

    def list_nodes(self, *, kind: NodeKind | str | None = None) -> list[GraphNode]: ...

    def relate(
        self,
        source_id: str,
        target_id: str,
        relation: EdgeRelation | str,
        *,
        weight: float = 1.0,
        confidence: float = 0.5,
        props: dict | None = None,
        edge_id: str | None = None,
    ) -> GraphEdge: ...

    def edges_from(
        self,
        source_id: str,
        *,
        relation: EdgeRelation | str | None = None,
    ) -> list[GraphEdge]: ...

    def edges_to(
        self,
        target_id: str,
        *,
        relation: EdgeRelation | str | None = None,
    ) -> list[GraphEdge]: ...

    def find_edges(
        self,
        *,
        relation: EdgeRelation | str | None = None,
        source_id: str | None = None,
        target_id: str | None = None,
    ) -> list[GraphEdge]: ...

    def stats(self) -> dict: ...
