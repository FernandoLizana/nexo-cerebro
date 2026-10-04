"""CLI for Debian packaging metadata / policy checks (S14)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.packaging.debian.control import package_manifest, render_control
from services.packaging.debian.layout import DebInstallLayout
from services.packaging.debian.policy import DebianPackagingError, assert_maintainer_script_safe, packaging_policy
from services.packaging.debian.unit import UNIT_NAME, user_unit_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexo-debpack",
        description="NEXO Debian packaging helpers — user-level; no forced root persistence.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("policy", help="Print packaging policy JSON")
    sub.add_parser("control", help="Print debian/control")
    sub.add_parser("unit", help="Print optional systemd --user unit")
    sub.add_parser("layout", help="Print default user layout + stop/disable commands")
    check = sub.add_parser("check-scripts", help="Validate maintainer scripts for persistence bans")
    check.add_argument("paths", nargs="+", type=Path)

    args = parser.parse_args(argv)

    if args.command == "policy":
        print(json.dumps(packaging_policy(), indent=2))
        return 0
    if args.command == "control":
        print(render_control(), end="")
        return 0
    if args.command == "unit":
        print(user_unit_text(), end="")
        return 0
    if args.command == "layout":
        layout = DebInstallLayout.default_user()
        print(
            json.dumps(
                {
                    "layout": layout.to_dict(),
                    "unit_name": UNIT_NAME,
                    "stop_disable": layout.stop_disable_commands(),
                    "manifest": package_manifest(),
                },
                indent=2,
            )
        )
        return 0
    if args.command == "check-scripts":
        try:
            for path in args.paths:
                assert_maintainer_script_safe(path.read_text(encoding="utf-8"))
        except DebianPackagingError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(json.dumps({"ok": True, "checked": [str(p) for p in args.paths]}))
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
