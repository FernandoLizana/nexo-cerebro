"""CLI for local knowledge graph demos (S10)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.knowledge.memory import InMemoryKnowledgeGraph
from services.knowledge.service import record_contradiction, record_interaction, record_support
from services.knowledge.types import EdgeRelation, NodeKind


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexo-knowledge",
        description="NEXO Knowledge Graph S10 — in-memory / JSON (no Neo4j).",
    )
    parser.add_argument(
        "--graph",
        type=Path,
        default=Path("data") / "nexo_knowledge" / "graph.json",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_n = sub.add_parser("add-node", help="Upsert a node")
    add_n.add_argument("--kind", required=True, choices=[k.value for k in NodeKind])
    add_n.add_argument("--id", required=True)
    add_n.add_argument("--label", default="")

    rel = sub.add_parser("relate", help="Add an allowlisted edge")
    rel.add_argument("--source", required=True)
    rel.add_argument("--target", required=True)
    rel.add_argument("--relation", required=True, choices=[r.value for r in EdgeRelation])
    rel.add_argument("--confidence", type=float, default=0.5)

    demo = sub.add_parser("demo", help="Record INTERACTED_WITH / SUPPORTS / CONTRADICTS")
    demo.add_argument("--a", default="being:alice")
    demo.add_argument("--b", default="being:bob")

    sub.add_parser("stats", help="Print graph stats")
    sub.add_parser("export", help="Print full JSON graph")

    args = parser.parse_args(argv)
    graph = InMemoryKnowledgeGraph.load_json(args.graph) if args.graph.is_file() else InMemoryKnowledgeGraph()

    if args.command == "add-node":
        node = graph.upsert_node(kind=args.kind, node_id=args.id, label=args.label)
        graph.save_json(args.graph)
        print(json.dumps(node.to_dict(), indent=2))
        return 0
    if args.command == "relate":
        edge = graph.relate(
            args.source,
            args.target,
            args.relation,
            confidence=args.confidence,
        )
        graph.save_json(args.graph)
        print(json.dumps(edge.to_dict(), indent=2))
        return 0
    if args.command == "demo":
        record_interaction(graph, args.a, args.b, confidence=0.8)
        record_support(graph, "concept:berries-near-water", "concept:obs-1", confidence=0.7)
        record_contradiction(graph, "concept:berries-near-water", "concept:berries-in-desert", confidence=0.6)
        graph.save_json(args.graph)
        print(json.dumps(graph.stats(), indent=2))
        return 0
    if args.command == "stats":
        print(json.dumps(graph.stats(), indent=2))
        return 0
    if args.command == "export":
        print(json.dumps(graph.to_dict(), indent=2))
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
