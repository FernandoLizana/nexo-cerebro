"""Verify a mobile-v1 envelope with an Ed25519 raw public key (32 bytes, hex).

For approved nodes the registered key must match. A key only present in the
message cannot prove identity.
"""

from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from protocols.mobile.canonical import canonical_bytes, signed_view
from protocols.mobile.envelope import validate_envelope


def verify_envelope(
    message: dict,
    *,
    now_ms: int | None = None,
    expected_public_key_hex: str | None = None,
) -> str | None:
    error = validate_envelope(message, now_ms=now_ms)
    if error:
        return error
    signature = str(message.get("signature") or "")
    public_hex = str(message.get("public_key_hex") or "")
    if len(public_hex) != 64 or len(signature) != 128:
        return "missing public_key_hex or signature"
    if expected_public_key_hex is not None:
        expected = str(expected_public_key_hex).strip().lower()
        if len(expected) != 64:
            return "registered key missing"
        if public_hex.lower() != expected:
            return "public key does not match registered node"
    try:
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex))
        key.verify(bytes.fromhex(signature), canonical_bytes(signed_view(message)))
    except Exception:
        return "invalid signature"
    return None
