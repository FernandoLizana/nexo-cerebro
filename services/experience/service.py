"""ExperienceStore facade — ingest always quarantines; promote is explicit."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from protocols.events.codec import decode_event
from services.experience.models import (
    ExperienceCandidate,
    ExperienceStatus,
    new_candidate_id,
)
from services.experience.store import AppendOnlyExperienceStore, ExperienceStoreError
from services.experience.validate import score_confidence, validate_candidate


class ExperienceError(ValueError):
    pass


class ExperienceStore:
    """Global experience pipeline (local disk).

    Rules:
    - ingest → always QUARANTINED (never PROMOTED)
    - validate → VALIDATED or REJECTED (never PROMOTED)
    - promote → explicit only, requires VALIDATED + confidence
    """

    def __init__(self, root: Path | str) -> None:
        self._store = AppendOnlyExperienceStore(root)
        self._keys: dict[str, str] = {}  # node_id → public_key_pem

    @property
    def root(self) -> Path:
        return self._store.root

    def register_node_key(self, node_id: str, public_key_pem: str) -> None:
        if not node_id or not public_key_pem:
            raise ExperienceError("node_id and public_key_pem required")
        self._keys[str(node_id)] = str(public_key_pem)

    def ingest(
        self,
        *,
        source_node_id: str,
        event: Mapping[str, Any],
        signature_hex: str | None = None,
        auto_validate: bool = False,
    ) -> ExperienceCandidate:
        """Append candidate to quarantine. Never promotes.

        ``auto_validate`` may run schema/signature checks but still will not promote.
        """
        # Fail closed on unknown event shapes early (still quarantine malformed? reject inline)
        try:
            decoded = decode_event(event)
            event_dict = decoded.to_dict()
        except Exception as exc:
            # Malformed events go straight to rejected without ever being "truth"
            candidate = ExperienceCandidate(
                candidate_id=new_candidate_id(),
                source_node_id=str(source_node_id),
                event=dict(event),
                status=ExperienceStatus.REJECTED,
                signature_hex=signature_hex,
                signature_ok=False,
                reject_reason=f"schema: {exc}",
                rejected_at=datetime.now(timezone.utc).isoformat(),
                validation_notes=[f"rejected:schema: {exc}"],
            )
            self._store.write(candidate)
            return candidate

        # Preserve caller signature on event if provided
        if signature_hex and not event_dict.get("signature_hex"):
            event_dict["signature_hex"] = signature_hex

        candidate = ExperienceCandidate(
            candidate_id=new_candidate_id(),
            source_node_id=str(source_node_id),
            event=event_dict,
            status=ExperienceStatus.QUARANTINED,
            signature_hex=signature_hex or event_dict.get("signature_hex"),
        )
        self._store.write(candidate)
        assert candidate.status is ExperienceStatus.QUARANTINED

        if auto_validate:
            candidate = self.validate(candidate.candidate_id)
            # Still must not be promoted
            assert candidate.status is not ExperienceStatus.PROMOTED
        return candidate

    def validate(self, candidate_id: str) -> ExperienceCandidate:
        try:
            candidate = self._store.load(candidate_id)
        except ExperienceStoreError as exc:
            raise ExperienceError(str(exc)) from exc
        if candidate.status is ExperienceStatus.PROMOTED:
            raise ExperienceError("already promoted; validation is a no-op path")
        pem = self._keys.get(candidate.source_node_id)
        candidate = validate_candidate(candidate, public_key_pem=pem)
        assert candidate.status is not ExperienceStatus.PROMOTED
        self._store.write(candidate)
        return candidate

    def promote(
        self,
        candidate_id: str,
        *,
        confidence: float | None = None,
        require_validated: bool = True,
    ) -> ExperienceCandidate:
        """Explicit promotion only. Quarantine never auto-calls this."""
        try:
            candidate = self._store.load(candidate_id)
        except ExperienceStoreError as exc:
            raise ExperienceError(str(exc)) from exc

        if candidate.status is ExperienceStatus.REJECTED:
            raise ExperienceError("cannot promote rejected candidate")
        if candidate.status is ExperienceStatus.PROMOTED:
            return candidate
        if require_validated and candidate.status is not ExperienceStatus.VALIDATED:
            raise ExperienceError(
                f"candidate must be VALIDATED before promote (got {candidate.status.value})"
            )
        if candidate.signature_ok is not True:
            raise ExperienceError("cannot promote without verified signature")

        conf = score_confidence(candidate) if confidence is None else float(confidence)
        conf = max(0.0, min(1.0, conf))
        candidate.status = ExperienceStatus.PROMOTED
        candidate.confidence = conf
        candidate.promoted_at = datetime.now(timezone.utc).isoformat()
        candidate.validation_notes = list(candidate.validation_notes) + [
            f"promoted_confidence={conf:.4f}"
        ]
        self._store.write(candidate)
        return candidate

    def list_quarantine(self) -> list[ExperienceCandidate]:
        return self._store.list_quarantine()

    def list_promoted(self) -> list[ExperienceCandidate]:
        return self._store.list_promoted()

    def get(self, candidate_id: str) -> ExperienceCandidate:
        try:
            return self._store.load(candidate_id)
        except ExperienceStoreError as exc:
            raise ExperienceError(str(exc)) from exc

    def stats(self) -> dict[str, Any]:
        return self._store.stats()
