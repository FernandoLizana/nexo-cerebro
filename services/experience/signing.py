"""Canonical signing for experience submissions (Ed25519 via NodeIdentity)."""

from __future__ import annotations

import hashlib
import json
from typing import Mapping

from services.node.identity import NodeIdentity


def event_payload_digest(event: Mapping[str, Any]) -> str:
    """Stable hash of event fields excluding signature."""
    body = {
        "version": event.get("version"),
        "event_id": event.get("event_id"),
        "event_type": event.get("event_type"),
        "tick": event.get("tick"),
        "timestamp": event.get("timestamp"),
        "payload": event.get("payload") or {},
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def experience_message(*, source_node_id: str, event: Mapping[str, Any]) -> bytes:
    digest = event_payload_digest(event)
    event_id = str(event.get("event_id") or "")
    event_type = str(event.get("event_type") or "")
    tick = int(event.get("tick") or 0)
    return (
        f"nexo-experience|{source_node_id}|{event_id}|{event_type}|{tick}|{digest}"
    ).encode("utf-8")


def verify_experience_signature(
    *,
    public_key_pem: str,
    source_node_id: str,
    event: Mapping[str, Any],
    signature: bytes,
) -> bool:
    return NodeIdentity.verify(
        public_key_pem,
        experience_message(source_node_id=source_node_id, event=event),
        signature,
    )


def sign_experience(
    identity: NodeIdentity,
    private_key,
    *,
    event: Mapping[str, Any],
) -> bytes:
    return identity.sign(
        private_key,
        experience_message(source_node_id=identity.node_id, event=event),
    )
