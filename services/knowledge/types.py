"""Knowledge graph type enumerations."""

from __future__ import annotations

from enum import Enum


class NodeKind(str, Enum):
    BEING = "BEING"
    NODE = "NODE"
    EXPERIMENT = "EXPERIMENT"
    CONCEPT = "CONCEPT"
    EVENT = "EVENT"
    WORLD = "WORLD"
    MEMORY = "MEMORY"


class EdgeRelation(str, Enum):
    """Core scientific edge vocabulary for Swarm S10."""

    INTERACTED_WITH = "INTERACTED_WITH"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    # Optional extensions (still allowlisted; not Neo4j-specific)
    PARTICIPATED_IN = "PARTICIPATED_IN"
    OBSERVED_IN = "OBSERVED_IN"
    DERIVED_FROM = "DERIVED_FROM"


ALLOWED_NODE_KINDS: frozenset[str] = frozenset(k.value for k in NodeKind)
ALLOWED_EDGE_RELATIONS: frozenset[str] = frozenset(r.value for r in EdgeRelation)
