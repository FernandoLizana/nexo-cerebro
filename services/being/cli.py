"""CLI — NEXO Character Creator / Being management (local, offline)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.being.creator import being_public_summary, create_being
from services.being.models import EXPERIMENTAL_DISCLAIMER, PERSONALITY_TRAITS, BeingArchetype, BeingSpecies
from services.being.store import BeingStore

DEFAULT_BEINGS = Path("data") / "nexo_node" / "beings"


def _parse_traits(pairs: list[str] | None) -> dict[str, float]:
    traits: dict[str, float] = {}
    for item in pairs or []:
        if "=" not in item:
            raise SystemExit(f"trait must be name=value, got {item!r}")
        key, raw = item.split("=", 1)
        traits[key.strip()] = float(raw)
    return traits


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexo-being",
        description=(
            "NEXO Character Creator — experimental synthetic Beings. "
            + EXPERIMENTAL_DISCLAIMER
        ),
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--beings-dir",
        type=Path,
        default=DEFAULT_BEINGS,
        help="Root directory for split Being stores",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", parents=[common], help="Create a Being")
    create.add_argument("--name", required=True)
    create.add_argument(
        "--species",
        required=True,
        choices=[s.value for s in BeingSpecies],
    )
    create.add_argument(
        "--archetype",
        default=BeingArchetype.CUSTOM.value,
        choices=[a.value for a in BeingArchetype],
    )
    create.add_argument("--creator-node", default="local-node")
    create.add_argument(
        "--trait",
        action="append",
        default=[],
        help=f"Experimental slider trait=0..1. Allowed: {', '.join(PERSONALITY_TRAITS)}",
    )
    create.add_argument("--interest", action="append", default=[])
    create.add_argument("--goal", action="append", default=[])
    create.add_argument("--fear", action="append", default=[])
    create.add_argument("--preference", action="append", default=[])
    create.add_argument("--style", default="neutral")
    create.add_argument("--cognitive-budget", type=float, default=1.0)
    create.add_argument("--memory-level", choices=["minimal", "standard", "rich"], default="standard")
    create.add_argument("--use-llm", action="store_true", help="Opt-in LLM (not for tiny animal tiers by default)")

    sub.add_parser("list", parents=[common], help="List Being ids")
    show = sub.add_parser("show", parents=[common], help="Show public Being summary")
    show.add_argument("--id", required=True, dest="being_id")

    traits = sub.add_parser("traits", help="List experimental personality slider names")
    _ = traits
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "traits":
        print(json.dumps({"traits": list(PERSONALITY_TRAITS), "disclaimer": EXPERIMENTAL_DISCLAIMER}, indent=2))
        return 0

    store = BeingStore(args.beings_dir)
    if args.command == "create":
        being = create_being(
            name=args.name,
            species=args.species,
            archetype=args.archetype,
            creator_node=args.creator_node,
            traits=_parse_traits(args.trait),
            interests=list(args.interest),
            goals=list(args.goal),
            simulated_fears=list(args.fear),
            preferences=list(args.preference),
            communication_style=args.style,
            cognitive_budget=args.cognitive_budget,
            memory_level=args.memory_level,
            use_llm=bool(args.use_llm),
            store=store,
        )
        print(json.dumps(being_public_summary(being), indent=2, ensure_ascii=False))
        return 0

    if args.command == "list":
        print(json.dumps({"beings": store.list_ids()}, indent=2))
        return 0

    if args.command == "show":
        being = store.load(args.being_id)
        print(json.dumps(being_public_summary(being), indent=2, ensure_ascii=False))
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
