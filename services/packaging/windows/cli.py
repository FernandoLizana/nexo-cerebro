"""Installer UX + packaging helpers CLI (S13)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from services.packaging.windows.consent import (
    CONSENT_STATEMENTS,
    ConsentError,
    require_consent,
    write_consent,
)
from services.packaging.windows.layout import (
    InstallLayout,
    simulate_uninstall,
    write_uninstall_manifest,
)
from services.packaging.windows.pipeline import build_pipeline_spec
from services.packaging.windows.silent_policy import SilentInstallError, reject_silent_flags


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    try:
        reject_silent_flags(raw)
    except SilentInstallError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(
        prog="nexo-winpack",
        description="NEXO Windows packaging UX — consent required; silent install forbidden.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show-consent", help="Print consent statements")
    acc = sub.add_parser("accept-consent", help="Record explicit consent (all statements)")
    acc.add_argument("--install-root", type=Path, default=None)
    acc.add_argument("--i-accept-all", action="store_true", required=True)

    plan = sub.add_parser("uninstall-plan", help="Print clean uninstall plan")
    plan.add_argument("--install-root", type=Path, default=None)

    un = sub.add_parser("uninstall", help="Run uninstall (default dry-run)")
    un.add_argument("--install-root", type=Path, default=None)
    un.add_argument("--execute", action="store_true", help="Actually delete install_root")

    sub.add_parser("pipeline", help="Print signed build pipeline spec (manual updates)")

    args = parser.parse_args(raw)
    layout = (
        InstallLayout(install_root=args.install_root, data_root=Path(args.install_root) / "data")
        if getattr(args, "install_root", None)
        else InstallLayout.default_user_layout()
    )

    if args.command == "show-consent":
        for i, line in enumerate(CONSENT_STATEMENTS, 1):
            print(f"{i}. {line}")
        return 0
    if args.command == "accept-consent":
        try:
            record = require_consent(accept_all=True)
        except ConsentError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        path = write_consent(layout.consent_path, record)
        write_uninstall_manifest(layout)
        print(json.dumps({"consent": str(path), "layout": layout.to_dict()}, indent=2))
        return 0
    if args.command == "uninstall-plan":
        path = write_uninstall_manifest(layout)
        print(path.read_text(encoding="utf-8"))
        return 0
    if args.command == "uninstall":
        result = simulate_uninstall(layout, dry_run=not args.execute)
        print(json.dumps(result, indent=2))
        return 0 if result.get("clean") or result.get("dry_run") else 1
    if args.command == "pipeline":
        print(json.dumps(build_pipeline_spec(), indent=2))
        return 0

    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
