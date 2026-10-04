"""mobile-v1 envelope. Signature covers canonical JSON excluding ``signature``."""

from __future__ import annotations

import time
import uuid
from typing import Any

from protocols.mobile import MAX_MESSAGE_BYTES, PROTOCOL_VERSION
from protocols.mobile.canonical import canonical_bytes, signed_view


REQUIRED = (
    "protocol_version",
    "message_id",
    "message_type",
    "node_id",
    "experiment_id",
    "timestamp",
    "nonce",
    "payload",
)


def build_envelope(
    *,
    message_type: str,
    node_id: str,
    payload: dict[str, Any],
    experiment_id: str = "",
    message_id: str | None = None,
    timestamp_ms: int | None = None,
    nonce: str | None = None,
) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "message_id": message_id or uuid.uuid4().hex,
        "message_type": message_type,
        "node_id": node_id,
        "experiment_id": experiment_id,
        "timestamp": int(timestamp_ms if timestamp_ms is not None else time.time() * 1000),
        "nonce": nonce or uuid.uuid4().hex,
        "payload": payload,
    }


def validate_envelope(message: dict[str, Any], *, now_ms: int | None = None) -> str | None:
    if not isinstance(message, dict):
        return "message must be an object"
    raw = canonical_bytes(signed_view(message))
    if len(raw) > MAX_MESSAGE_BYTES:
        return "message too large"
    for key in REQUIRED:
        if key not in message:
            return f"missing {key}"
    if message["protocol_version"] != PROTOCOL_VERSION:
        return "unknown protocol version"
    if not isinstance(message["payload"], dict):
        return "payload must be an object"
    if not isinstance(message["timestamp"], int) or isinstance(message["timestamp"], bool):
        return "timestamp must be unix millis int"
    now = int(now_ms if now_ms is not None else time.time() * 1000)
    if abs(now - int(message["timestamp"])) > 300_000:
        return "timestamp outside replay window"
    return None
