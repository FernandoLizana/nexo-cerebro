"""Console entry for frozen NEXO-Node.exe (S13).

Requires prior consent file beside the executable (or under install root).
Kill switch: ``NEXO-Node.exe stop``.
"""

from __future__ import annotations

import sys
from pathlib import Path

from services.node.cli import main as node_main
from services.packaging.windows.consent import ConsentError, ensure_consent_file
from services.packaging.windows.silent_policy import SilentInstallError, reject_silent_flags


def _install_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        reject_silent_flags(args)
    except SilentInstallError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    # Allow stop/status without re-prompting consent UX mid-kill-switch.
    if args and args[0] in {"stop", "status"}:
        return node_main(args)

    consent_path = _install_root() / "consent.json"
    try:
        ensure_consent_file(consent_path)
    except ConsentError as exc:
        print(str(exc), file=sys.stderr)
        print("Run: nexo-winpack accept-consent --i-accept-all", file=sys.stderr)
        return 2
    return node_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
