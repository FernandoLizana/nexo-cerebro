"""Loopback-only dashboard auth — shared secret on localhost."""

from __future__ import annotations

import secrets
from pathlib import Path


class DashboardAuthError(PermissionError):
    pass


class LocalDashboardAuth:
    """Simple bearer token for local scientific UI (not multi-tenant IAM)."""

    HEADER = "X-Nexo-Dashboard-Token"

    def __init__(self, token: str | None = None) -> None:
        self.token = (token or secrets.token_urlsafe(24)).strip()
        if len(self.token) < 16:
            raise DashboardAuthError("dashboard token too short")

    @classmethod
    def load_or_create(cls, path: Path | str) -> LocalDashboardAuth:
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
            raise DashboardAuthError("invalid or missing dashboard token")
