"""Loopback bind policy shared by long-running Swarm surfaces."""

from __future__ import annotations

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def is_loopback_host(host: str) -> bool:
    return str(host).strip().lower() in {h.lower() for h in LOOPBACK_HOSTS} or str(host) in LOOPBACK_HOSTS


def assert_loopback_host(host: str, *, context: str = "bind") -> None:
    if not is_loopback_host(host):
        raise ValueError(
            f"Refusing non-loopback {context}: {host!r}. "
            "Use 127.0.0.1 / localhost / ::1 only."
        )
