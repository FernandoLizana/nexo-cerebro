"""Experience candidate models — quarantine by default."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


EXPERIENCE_FORMAT = "experience-v1"


class ExperienceStatus(str, Enum):
    QUARANTINED = "QUARANTINED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    PROMOTED = "PROMOTED"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_candidate_id() -> str:
    return f"exp-{uuid.uuid4().hex[:16]}"


@dataclass
class ExperienceCandidate:
    """Shared-experience candidate. Starts quarantined; promotion is explicit only."""

    candidate_id: str
    source_node_id: str
    event: dict[str, Any]
    status: ExperienceStatus = ExperienceStatus.QUARANTINED
    signature_hex: str | None = None
    signature_ok: bool | None = None
    validation_notes: list[str] = field(default_factory=list)
    confidence: float | None = None
    promoted_at: str | None = None
    rejected_at: str | None = None
    reject_reason: str | None = None
    received_at: str = field(default_factory=_utc_now)
    format_version: str = EXPERIENCE_FORMAT

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_version": self.format_version,
            "candidate_id": self.candidate_id,
            "source_node_id": self.source_node_id,
            "event": dict(self.event),
            "status": self.status.value,
            "signature_hex": self.signature_hex,
            "signature_ok": self.signature_ok,
            "validation_notes": list(self.validation_notes),
            "confidence": None if self.confidence is None else float(self.confidence),
            "promoted_at": self.promoted_at,
            "rejected_at": self.rejected_at,
            "reject_reason": self.reject_reason,
            "received_at": self.received_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExperienceCandidate:
        status_raw = str(data.get("status") or ExperienceStatus.QUARANTINED.value)
        try:
            status = ExperienceStatus(status_raw)
        except ValueError:
            status = ExperienceStatus.QUARANTINED
        conf = data.get("confidence")
        return cls(
            candidate_id=str(data.get("candidate_id") or new_candidate_id()),
            source_node_id=str(data.get("source_node_id") or ""),
            event=dict(data.get("event") or {}),
            status=status,
            signature_hex=None if data.get("signature_hex") is None else str(data.get("signature_hex")),
            signature_ok=None if data.get("signature_ok") is None else bool(data.get("signature_ok")),
            validation_notes=[str(x) for x in list(data.get("validation_notes") or [])],
            confidence=None if conf is None else float(conf),
            promoted_at=None if data.get("promoted_at") is None else str(data.get("promoted_at")),
            rejected_at=None if data.get("rejected_at") is None else str(data.get("rejected_at")),
            reject_reason=None if data.get("reject_reason") is None else str(data.get("reject_reason")),
            received_at=str(data.get("received_at") or _utc_now()),
            format_version=str(data.get("format_version") or EXPERIENCE_FORMAT),
        )
