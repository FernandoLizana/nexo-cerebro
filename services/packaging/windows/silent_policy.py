"""Reject silent / unattended Windows installer flags (S13)."""

from __future__ import annotations

# Common silent/unattended switches across NSIS/Inno/MSI/custom CLIs.
SILENT_FLAGS: frozenset[str] = frozenset(
    {
        "/s",
        "/S",
        "/silent",
        "/SILENT",
        "/verysilent",
        "/VERYSILENT",
        "/quiet",
        "/QUIET",
        "/qn",
        "/QN",
        "/q",
        "/Q",
        "--silent",
        "--quiet",
        "--unattended",
        "/norestart",  # often paired with silent enterprise installs — still require UX
    }
)


class SilentInstallError(ValueError):
    pass


def reject_silent_flags(argv: list[str] | tuple[str, ...] | None) -> None:
    """Fail closed if any silent/unattended flag is present."""
    args = [str(a) for a in (argv or [])]
    for arg in args:
        key = arg.split("=", 1)[0]
        if key in SILENT_FLAGS or key.lower() in {f.lower() for f in SILENT_FLAGS}:
            raise SilentInstallError(
                f"silent/unattended install flag rejected: {arg!r}. "
                "NEXO Windows install requires explicit consent UX."
            )
        lower = arg.lower()
        if lower.startswith("/silent") or lower.startswith("--silent"):
            raise SilentInstallError(f"silent/unattended install flag rejected: {arg!r}")
