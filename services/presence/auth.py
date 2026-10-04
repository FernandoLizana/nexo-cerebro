"""Loopback presence-hub auth — shared secret for mutating routes."""

from __future__ import annotations

import secrets
from pathlib import Path
from urllib.parse import urlparse


class PresenceAuthError(PermissionError):
    pass


class LocalPresenceAuth:
    """Bearer token for local visual hub writes (not multi-tenant IAM)."""

    HEADER = "X-Nexo-Presence-Token"

    def __init__(self, token: str | None = None) -> None:
        self.token = (token or secrets.token_urlsafe(24)).strip()
        if len(self.token) < 16:
            raise PresenceAuthError("presence token too short")

    @classmethod
    def load_or_create(cls, path: Path | str) -> LocalPresenceAuth:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_file():
            raw = path.read_text(encoding="utf-8").strip()
            return cls(raw)
        auth = cls()
        path.write_text(auth.token + "\n", encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
        return auth

    def check(self, provided: str | None) -> None:
        if not provided or not secrets.compare_digest(str(provided), self.token):
            raise PresenceAuthError("invalid or missing presence token")


_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
# Android emulator special alias to the host machine (lab only; not a public bind).
_LAB_EMULATOR_HOSTS = frozenset({"10.0.2.2"})
_ALLOWED_MUTATION_HOSTS = _LOOPBACK_HOSTS | _LAB_EMULATOR_HOSTS


def _normalize_host(host_header: str | None) -> str:
    raw = str(host_header or "").strip().lower()
    if not raw:
        return ""
    # Strip port / brackets: "127.0.0.1:8770", "[::1]:8770"
    if raw.startswith("["):
        end = raw.find("]")
        return raw[1:end] if end > 0 else raw
    if raw.count(":") == 1:
        return raw.rsplit(":", 1)[0]
    return raw.split("%", 1)[0]


def host_is_loopback(host_header: str | None) -> bool:
    """True for loopback or the Android-emulator host alias (10.0.2.2)."""
    return _normalize_host(host_header) in _ALLOWED_MUTATION_HOSTS


def origin_is_loopback_or_absent(origin: str | None) -> bool:
    """Absent Origin is allowed for non-browser clients that still present the token.

    When Origin is present (typical browser fetch), it must be loopback http(s)
    or the emulator lab alias.
    """
    raw = str(origin or "").strip()
    if not raw:
        return True
    if raw.lower() == "null":
        return False
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower()
    return host in _ALLOWED_MUTATION_HOSTS
