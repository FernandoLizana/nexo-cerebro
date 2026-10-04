"""S10 — Knowledge Graph contract tests (in-memory; no Neo4j)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services.knowledge.memory import InMemoryKnowledgeGraph, KnowledgeGraphError
from services.knowledge.protocol import KnowledgeGraph
from services.knowledge.service import record_contradiction, record_interaction, record_support
from services.knowledge.types import EdgeRelation, NodeKind

ROOT = Path(__file__).resolve().parents[1]
KG_PKG = ROOT / "services" / "knowledge"


def test_in_memory_satisfies_protocol() -> None:
    g = InMemoryKnowledgeGraph()
    assert isinstance(g, KnowledgeGraph)


def test_record_interacted_with_supports_contradicts(tmp_path: Path) -> None:
    g = InMemoryKnowledgeGraph()
    e1 = record_interaction(g, "being:a", "being:b", confidence=0.9)
    assert e1.relation is EdgeRelation.INTERACTED_WITH
    e2 = record_support(g, "concept:claim", "concept:evidence", confidence=0.75)
    assert e2.relation is EdgeRelation.SUPPORTS
    e3 = record_contradiction(g, "concept:claim", "concept:rival", confidence=0.55)
    assert e3.relation is EdgeRelation.CONTRADICTS

    assert len(g.edges_from("being:a", relation=EdgeRelation.INTERACTED_WITH)) == 1
    assert len(g.find_edges(relation=EdgeRelation.SUPPORTS)) == 1
    assert len(g.find_edges(relation=EdgeRelation.CONTRADICTS)) == 1

    stats = g.stats()
    assert stats["neo4j_required"] is False
    assert stats["backend"] == "in_memory"
    assert stats["nodes"] >= 4
    assert stats["edges"] == 3

    path = tmp_path / "g.json"
    g.save_json(path)
    g2 = InMemoryKnowledgeGraph.load_json(path)
    assert g2.stats()["edges"] == 3
    assert g2.get_node("being:a") is not None


def test_unknown_relation_and_missing_nodes_fail_closed() -> None:
    g = InMemoryKnowledgeGraph()
    g.upsert_node(kind=NodeKind.BEING, node_id="being:x")
    with pytest.raises((KnowledgeGraphError, ValueError)):
        g.relate("being:x", "being:missing", EdgeRelation.INTERACTED_WITH)
    with pytest.raises(ValueError):
        g.relate("being:x", "being:x", "NOT_A_RELATION")  # type: ignore[arg-type]


def test_no_neo4j_dependency_in_package() -> None:
    for path in KG_PKG.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "from neo4j" not in text
        assert "import neo4j" not in text
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in {
                        "neo4j",
                        "socket",
                        "subprocess",
                        "requests",
                    }
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in {
                    "neo4j",
                    "socket",
                    "subprocess",
                    "requests",
                }


def test_node_kinds_cover_swarm_entities() -> None:
    names = {k.value for k in NodeKind}
    assert {"BEING", "NODE", "EXPERIMENT", "CONCEPT"}.issubset(names)
