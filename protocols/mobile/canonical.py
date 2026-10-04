"""Canonical JSON for mobile-v1 signatures.

Python ``json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=False)``.
Kotlin must match this byte-for-byte. Floats are rejected: use ints and strings.
"""

from __future__ import annotations

import json
from typing import Any


def _reject_floats(value: Any) -> None:
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return
    if isinstance(value, float):
        raise ValueError("floats are forbidden in mobile-v1 canonical JSON")
    if isinstance(value, list):
        for item in value:
            _reject_floats(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_floats(item)
        return
    raise ValueError(f"unsupported canonical type: {type(value).__name__}")


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    _reject_floats(payload)
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text.encode("utf-8")


def signed_view(message: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in message.items() if k != "signature"}
