"""Explicit owner consent for Windows install / first-run (S13)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CONSENT_VERSION = "nexo-windows-consent-v1"

CONSENT_STATEMENTS: tuple[str, ...] = (
    "I understand NEXO Node is a voluntary scientific laboratory runtime.",
    "I understand the node does not install silent background services.",
    "I can STOP NEXO NODE (kill switch) at any time.",
    "I consent to local storage of node identity keys under my chosen data directory.",
    "I understand updates are manual (no forced auto-update channel in S13).",
)


class ConsentError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ConsentRecord:
    accepted: bool
    accepted_at: str
    statements: tuple[str, ...]
    version: str = CONSENT_VERSION
    installer_channel: str = "manual"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "accepted": self.accepted,
            "accepted_at": self.accepted_at,
            "statements": list(self.statements),
            "installer_channel": self.installer_channel,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConsentRecord:
        return cls(
            accepted=bool(data.get("accepted")),
            accepted_at=str(data.get("accepted_at") or ""),
            statements=tuple(str(s) for s in list(data.get("statements") or [])),
            version=str(data.get("version") or CONSENT_VERSION),
            installer_channel=str(data.get("installer_channel") or "manual"),
        )


def require_consent(*, accept_all: bool, accept_flags: list[bool] | None = None) -> ConsentRecord:
    """Gate: every consent statement must be explicitly accepted. No defaults."""
    if accept_flags is not None:
        flags = [bool(f) for f in accept_flags]
    else:
        flags = [bool(accept_all)] * len(CONSENT_STATEMENTS)
    if len(flags) != len(CONSENT_STATEMENTS):
        raise ConsentError("consent flag count mismatch")
    if not all(flags):
        raise ConsentError("all consent statements must be accepted explicitly")
    return ConsentRecord(
        accepted=True,
        accepted_at=datetime.now(timezone.utc).isoformat(),
        statements=CONSENT_STATEMENTS,
    )


def write_consent(path: Path | str, record: ConsentRecord) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def read_consent(path: Path | str) -> ConsentRecord | None:
    path = Path(path)
    if not path.is_file():
        return None
    return ConsentRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))


def ensure_consent_file(path: Path | str) -> ConsentRecord:
    record = read_consent(path)
    if record is None or not record.accepted:
        raise ConsentError("missing or incomplete consent record; run installer UX first")
    if record.version != CONSENT_VERSION:
        raise ConsentError(f"consent version mismatch: {record.version}")
    return record
