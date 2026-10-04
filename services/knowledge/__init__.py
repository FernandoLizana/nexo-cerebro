"""NEXO Knowledge Graph (S10) — interface-first, pluggable backends.

Default backend is in-memory. No Neo4j (or any graph DB) required.
"""

from __future__ import annotations

from services.knowledge.memory import InMemoryKnowledgeGraph, KnowledgeGraphError
from services.knowledge.models import GraphEdge, GraphNode
from services.knowledge.protocol import KnowledgeGraph
from services.knowledge.types import EdgeRelation, NodeKind

__all__ = [
    "EdgeRelation",
    "GraphEdge",
    "GraphNode",
    "InMemoryKnowledgeGraph",
    "KnowledgeGraph",
    "KnowledgeGraphError",
    "NodeKind",
]
