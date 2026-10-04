"""CLI for per-Being local memory (S8)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.memory.local.store import LocalMemoryStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexo-memory",
        description="NEXO Local Memory S8 — per-Being episodic/semantic/relationship store.",
    )
    parser.add_argument(
        "--beings-root",
        type=Path,
        default=Path("data") / "nexo_node" / "beings",
        help="Root directory containing <being_id>/ trees",
    )
    parser.add_argument("--being-id", required=True, help="Target Being id")
    sub = parser.add_subparsers(dest="command", required=True)

    add_ep = sub.add_parser("add-episodic", help="Append an episodic memory")
    add_ep.add_argument("--content", required=True)
    add_ep.add_argument("--importance", type=float, default=0.5)

    add_sem = sub.add_parser("add-semantic", help="Append a semantic memory")
    add_sem.add_argument("--content", required=True)
    add_sem.add_argument("--importance", type=float, default=0.6)

    add_rel = sub.add_parser("add-relationship", help="Upsert a relationship memory")
    add_rel.add_argument("--peer", required=True)
    add_rel.add_argument("--type", dest="relation_type", default="known")
    add_rel.add_argument("--strength", type=float, default=0.5)
    add_rel.add_argument("--notes", default="")

    recall = sub.add_parser("recall", help="Bounded recall (never wholesale dump)")
    recall.add_argument("--query", default=None)
    recall.add_argument("--limit", type=int, default=8)

    prompt = sub.add_parser("prompt-context", help="Build bounded LLM context snippet")
    prompt.add_argument("--query", default=None)
    prompt.add_argument("--limit", type=int, default=5)
    prompt.add_argument("--max-chars", type=int, default=1500)

    decay = sub.add_parser("decay", help="Apply decay pass")
    decay.add_argument("--amount", type=float, default=0.05)

    sub.add_parser("stats", help="Print store counts")

    args = parser.parse_args(argv)
    store = LocalMemoryStore.for_being(args.beings_root, args.being_id)

    if args.command == "add-episodic":
        entry = store.add_episodic(args.content, importance=args.importance)
        print(json.dumps(entry.to_dict(), indent=2))
        return 0
    if args.command == "add-semantic":
        entry = store.add_semantic(args.content, importance=args.importance)
        print(json.dumps(entry.to_dict(), indent=2))
        return 0
    if args.command == "add-relationship":
        rel = store.upsert_relationship(
            args.peer,
            relation_type=args.relation_type,
            strength=args.strength,
            notes=args.notes,
        )
        print(json.dumps(rel.to_dict(), indent=2))
        return 0
    if args.command == "recall":
        items = store.recall(args.query, limit=args.limit)
        print(json.dumps([i.to_dict() for i in items], indent=2))
        return 0
    if args.command == "prompt-context":
        text = store.prompt_context(args.query, limit=args.limit, max_chars=args.max_chars)
        print(text)
        return 0
    if args.command == "decay":
        print(json.dumps(store.apply_decay(args.amount), indent=2))
        return 0
    if args.command == "stats":
        print(json.dumps(store.stats(), indent=2))
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
