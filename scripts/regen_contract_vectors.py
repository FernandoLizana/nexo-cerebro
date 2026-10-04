#!/usr/bin/env python3
"""Regenerate mobile-v1 golden contract vectors with a fixed Ed25519 seed.

Run by hand when the envelope or creature-tier0 format changes on purpose:

    python scripts/regen_contract_vectors.py

Tests under tests/mobile_contract/ only *read* the vectors and compare.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocols.mobile.canonical import canonical_bytes, signed_view
from protocols.mobile.creature_tier0 import run_mobile_creature
from protocols.mobile.envelope import build_envelope

VECTORS = ROOT / "tests" / "mobile_contract" / "vectors"

# Deterministic fixture key for golden signatures. Not a production secret.
GOLDEN_ED25519_SEED = bytes.fromhex("01" * 32)


def _sign(key: Ed25519PrivateKey, message: dict) -> dict:
    signed = dict(message)
    signed["public_key_hex"] = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    ).hex()
    raw = canonical_bytes(signed_view(signed))
    signed["signature"] = key.sign(raw).hex()
    return signed


def main() -> int:
    VECTORS.mkdir(parents=True, exist_ok=True)

    creature = run_mobile_creature(seed=7, ticks=5, being_id="being-1")
    (VECTORS / "creature_seed7.json").write_text(
        json.dumps(creature, indent=2) + "\n", encoding="utf-8"
    )

    key = Ed25519PrivateKey.from_private_bytes(GOLDEN_ED25519_SEED)
    message = build_envelope(
        message_type="heartbeat",
        node_id="node-test",
        payload={"seq": 1},
        timestamp_ms=1_700_000_000_000,
        nonce="n1",
        message_id="m1",
    )
    signed = _sign(key, message)
    (VECTORS / "heartbeat_signed.json").write_text(
        json.dumps(signed, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {VECTORS / 'creature_seed7.json'}")
    print(f"wrote {VECTORS / 'heartbeat_signed.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
