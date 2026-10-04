"""CLI for Global Experience Store demos (S9)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from protocols.events.codec import encode_event
from services.experience.service import ExperienceStore
from services.experience.signing import sign_experience
from services.node.identity import load_or_create_identity


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexo-experience",
        description="NEXO Experience S9 — quarantine → validate → explicit promote.",
    )
    parser.add_argument(
        "--store-dir",
        type=Path,
        default=Path("data") / "nexo_experience",
    )
    parser.add_argument(
        "--node-dir",
        type=Path,
        default=Path("data") / "nexo_node",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    submit = sub.add_parser("submit-demo", help="Sign + quarantine a KNOWLEDGE_CANDIDATE")
    submit.add_argument("--claim", required=True)
    submit.add_argument("--confidence", type=float, default=0.6)
    submit.add_argument("--auto-validate", action="store_true")

    val = sub.add_parser("validate", help="Validate a quarantined candidate")
    val.add_argument("--id", required=True)

    promo = sub.add_parser("promote", help="Explicitly promote a VALIDATED candidate")
    promo.add_argument("--id", required=True)
    promo.add_argument("--confidence", type=float, default=None)

    sub.add_parser("stats", help="Print store counts")
    sub.add_parser("list-quarantine", help="List quarantine candidates")
    sub.add_parser("list-promoted", help="List promoted candidates")

    args = parser.parse_args(argv)
    store = ExperienceStore(args.store_dir)
    identity, private_key = load_or_create_identity(args.node_dir, node_name="experience-demo")
    store.register_node_key(identity.node_id, identity.public_key_pem)

    if args.command == "submit-demo":
        event = encode_event(
            event_type="KNOWLEDGE_CANDIDATE",
            tick=1,
            payload={"claim": args.claim, "confidence": args.confidence},
        )
        sig = sign_experience(identity, private_key, event=event)
        cand = store.ingest(
            source_node_id=identity.node_id,
            event=event,
            signature_hex=sig.hex(),
            auto_validate=bool(args.auto_validate),
        )
        print(json.dumps(cand.to_dict(), indent=2))
        return 0
    if args.command == "validate":
        print(json.dumps(store.validate(args.id).to_dict(), indent=2))
        return 0
    if args.command == "promote":
        print(
            json.dumps(
                store.promote(args.id, confidence=args.confidence).to_dict(),
                indent=2,
            )
        )
        return 0
    if args.command == "stats":
        print(json.dumps(store.stats(), indent=2))
        return 0
    if args.command == "list-quarantine":
        print(json.dumps([c.to_dict() for c in store.list_quarantine()], indent=2))
        return 0
    if args.command == "list-promoted":
        print(json.dumps([c.to_dict() for c in store.list_promoted()], indent=2))
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
