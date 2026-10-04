"""In-memory KnowledgeGraph backend — default for S10 (no Neo4j)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.knowledge.models import GraphEdge, GraphNode, new_edge_id, new_node_id
from services.knowledge.types import (
    ALLOWED_EDGE_RELATIONS,
    ALLOWED_NODE_KINDS,
    EdgeRelation,
    NodeKind,
)


class KnowledgeGraphError(ValueError):
    pass


class InMemoryKnowledgeGraph:
    """Dict-backed graph satisfying ``KnowledgeGraph`` contract."""

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}

    def upsert_node(
        self,
        *,
        kind: NodeKind | str,
        node_id: str | None = None,
        label: str = "",
        props: dict | None = None,
    ) -> GraphNode:
        kind_e = kind if isinstance(kind, NodeKind) else NodeKind(str(kind))
        if kind_e.value not in ALLOWED_NODE_KINDS:
            raise KnowledgeGraphError(f"node kind not allowlisted: {kind}")
        nid = node_id or new_node_id(kind_e)
        existing = self._nodes.get(nid)
        merged_props = dict(existing.props) if existing else {}
        merged_props.update(dict(props or {}))
        if existing is None:
            node = GraphNode(node_id=nid, kind=kind_e, label=label, props=merged_props)
        else:
            node = GraphNode(
                node_id=nid,
                kind=kind_e,
                label=label or existing.label,
                props=merged_props,
                created_at=existing.created_at,
            )
        self._nodes[nid] = node
        return node

    def get_node(self, node_id: str) -> GraphNode | None:
        return self._nodes.get(node_id)

    def list_nodes(self, *, kind: NodeKind | str | None = None) -> list[GraphNode]:
        if kind is None:
            return list(self._nodes.values())
        kind_e = kind if isinstance(kind, NodeKind) else NodeKind(str(kind))
        return [n for n in self._nodes.values() if n.kind is kind_e]

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
    ) -> GraphEdge:
        if source_id not in self._nodes:
            raise KnowledgeGraphError(f"unknown source node: {source_id}")
        if target_id not in self._nodes:
            raise KnowledgeGraphError(f"unknown target node: {target_id}")
        rel = relation if isinstance(relation, EdgeRelation) else EdgeRelation(str(relation))
        if rel.value not in ALLOWED_EDGE_RELATIONS:
            raise KnowledgeGraphError(f"edge relation not allowlisted: {relation}")
        eid = edge_id or new_edge_id()
        edge = GraphEdge(
            edge_id=eid,
            source_id=source_id,
            target_id=target_id,
            relation=rel,
            weight=float(weight),
            confidence=float(confidence),
            props=dict(props or {}),
        )
        self._edges[eid] = edge
        return edge

    def edges_from(
        self,
        source_id: str,
        *,
        relation: EdgeRelation | str | None = None,
    ) -> list[GraphEdge]:
        return self.find_edges(source_id=source_id, relation=relation)

    def edges_to(
        self,
        target_id: str,
        *,
        relation: EdgeRelation | str | None = None,
    ) -> list[GraphEdge]:
        return self.find_edges(target_id=target_id, relation=relation)

    def find_edges(
        self,
        *,
        relation: EdgeRelation | str | None = None,
        source_id: str | None = None,
        target_id: str | None = None,
    ) -> list[GraphEdge]:
        rel_e: EdgeRelation | None = None
        if relation is not None:
            rel_e = relation if isinstance(relation, EdgeRelation) else EdgeRelation(str(relation))
        out: list[GraphEdge] = []
        for edge in self._edges.values():
            if source_id is not None and edge.source_id != source_id:
                continue
            if target_id is not None and edge.target_id != target_id:
                continue
            if rel_e is not None and edge.relation is not rel_e:
                continue
            out.append(edge)
        return out

    def stats(self) -> dict[str, Any]:
        by_kind: dict[str, int] = {}
        for n in self._nodes.values():
            by_kind[n.kind.value] = by_kind.get(n.kind.value, 0) + 1
        by_rel: dict[str, int] = {}
        for e in self._edges.values():
            by_rel[e.relation.value] = by_rel.get(e.relation.value, 0) + 1
        return {
            "backend": "in_memory",
            "neo4j_required": False,
            "nodes": len(self._nodes),
            "edges": len(self._edges),
            "nodes_by_kind": by_kind,
            "edges_by_relation": by_rel,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": "knowledge-graph-v1",
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges.values()],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> InMemoryKnowledgeGraph:
        g = cls()
        data = dict(data or {})
        for raw in list(data.get("nodes") or []):
            node = GraphNode.from_dict(raw)
            g._nodes[node.node_id] = node
        for raw in list(data.get("edges") or []):
            edge = GraphEdge.from_dict(raw)
            g._edges[edge.edge_id] = edge
        return g

    def save_json(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load_json(cls, path: Path | str) -> InMemoryKnowledgeGraph:
        path = Path(path)
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
