"""Thin helpers over KnowledgeGraph backends."""

from __future__ import annotations

from services.knowledge.memory import InMemoryKnowledgeGraph, KnowledgeGraphError
from services.knowledge.models import GraphEdge, GraphNode
from services.knowledge.types import EdgeRelation, NodeKind


def record_interaction(
    graph: InMemoryKnowledgeGraph,
    being_a: str,
    being_b: str,
    *,
    confidence: float = 0.6,
    props: dict | None = None,
) -> GraphEdge:
    """Ensure Being nodes exist and record INTERACTED_WITH."""
    graph.upsert_node(kind=NodeKind.BEING, node_id=being_a, label=being_a)
    graph.upsert_node(kind=NodeKind.BEING, node_id=being_b, label=being_b)
    return graph.relate(
        being_a,
        being_b,
        EdgeRelation.INTERACTED_WITH,
        confidence=confidence,
        props=props,
    )


def record_support(
    graph: InMemoryKnowledgeGraph,
    claim_id: str,
    evidence_id: str,
    *,
    confidence: float = 0.5,
    claim_label: str = "",
    evidence_label: str = "",
) -> GraphEdge:
    """Evidence SUPPORTS claim (both CONCEPT nodes by default)."""
    graph.upsert_node(kind=NodeKind.CONCEPT, node_id=evidence_id, label=evidence_label or evidence_id)
    graph.upsert_node(kind=NodeKind.CONCEPT, node_id=claim_id, label=claim_label or claim_id)
    return graph.relate(
        evidence_id,
        claim_id,
        EdgeRelation.SUPPORTS,
        confidence=confidence,
    )


def record_contradiction(
    graph: InMemoryKnowledgeGraph,
    claim_a: str,
    claim_b: str,
    *,
    confidence: float = 0.5,
) -> GraphEdge:
    """claim_a CONTRADICTS claim_b."""
    graph.upsert_node(kind=NodeKind.CONCEPT, node_id=claim_a, label=claim_a)
    graph.upsert_node(kind=NodeKind.CONCEPT, node_id=claim_b, label=claim_b)
    return graph.relate(
        claim_a,
        claim_b,
        EdgeRelation.CONTRADICTS,
        confidence=confidence,
    )


__all__ = [
    "GraphEdge",
    "GraphNode",
    "InMemoryKnowledgeGraph",
    "KnowledgeGraphError",
    "record_contradiction",
    "record_interaction",
    "record_support",
]
