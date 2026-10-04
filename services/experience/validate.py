"""Validation workers — schema + signature checks; never promote."""

from __future__ import annotations

from typing import Any, Mapping

from protocols.events.codec import EventProtocolError, decode_event
from services.experience.models import ExperienceCandidate, ExperienceStatus
from services.experience.signing import verify_experience_signature


class ExperienceValidationError(ValueError):
    """Candidate failed validation (stays out of promoted set)."""


def validate_candidate(
    candidate: ExperienceCandidate,
    *,
    public_key_pem: str | None,
) -> ExperienceCandidate:
    """Run validation. On success → VALIDATED (still not PROMOTED). On failure → REJECTED."""
    notes: list[str] = list(candidate.validation_notes)
    original_event = dict(candidate.event)

    try:
        decoded = decode_event(candidate.event)
        notes.append("event_schema_ok")
    except EventProtocolError as exc:
        return _reject(candidate, reason=f"schema: {exc}", notes=notes)

    if not candidate.source_node_id:
        return _reject(candidate, reason="missing source_node_id", notes=notes)

    if not candidate.signature_hex:
        return _reject(candidate, reason="missing signature", notes=notes)

    if not public_key_pem:
        return _reject(candidate, reason="missing public key for source node", notes=notes)

    try:
        sig = bytes.fromhex(candidate.signature_hex)
    except ValueError:
        return _reject(candidate, reason="malformed signature hex", notes=notes)

    # Verify against the submitted event body (pre-rewrite) so sanitize round-trips don't break auth.
    ok = verify_experience_signature(
        public_key_pem=public_key_pem,
        source_node_id=candidate.source_node_id,
        event=original_event,
        signature=sig,
    )
    candidate.signature_ok = ok
    if not ok:
        return _reject(candidate, reason="bad signature", notes=notes)

    notes.append("signature_ok")
    candidate.event = decoded.to_dict()
    # Content policy: refuse empty knowledge candidates
    if decoded.event_type.value == "KNOWLEDGE_CANDIDATE":
        claim = str((decoded.payload or {}).get("claim") or "").strip()
        if not claim:
            return _reject(candidate, reason="empty knowledge claim", notes=notes)
        notes.append("knowledge_claim_present")

    candidate.status = ExperienceStatus.VALIDATED
    candidate.validation_notes = notes
    candidate.reject_reason = None
    candidate.rejected_at = None
    # CRITICAL: never set PROMOTED here
    assert candidate.status is not ExperienceStatus.PROMOTED
    return candidate


def _reject(
    candidate: ExperienceCandidate,
    *,
    reason: str,
    notes: list[str],
) -> ExperienceCandidate:
    from datetime import datetime, timezone

    candidate.status = ExperienceStatus.REJECTED
    candidate.reject_reason = reason
    candidate.rejected_at = datetime.now(timezone.utc).isoformat()
    candidate.validation_notes = notes + [f"rejected:{reason}"]
    candidate.confidence = None
    candidate.promoted_at = None
    return candidate


def score_confidence(candidate: ExperienceCandidate, *, base: float = 0.5) -> float:
    """Heuristic confidence for promoted knowledge (scientific candidate, not truth)."""
    score = max(0.0, min(1.0, float(base)))
    if candidate.signature_ok:
        score = min(1.0, score + 0.25)
    event_type = str((candidate.event or {}).get("event_type") or "")
    if event_type == "KNOWLEDGE_CANDIDATE":
        payload = dict((candidate.event or {}).get("payload") or {})
        reported = payload.get("confidence")
        if reported is not None:
            score = (score + float(reported)) / 2.0
    return float(max(0.0, min(1.0, score)))
