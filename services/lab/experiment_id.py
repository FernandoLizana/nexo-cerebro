"""Reproducible experiment identifiers for multi-device labs."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def make_experiment_id(
    *,
    lab_name: str,
    seed: int,
    device_ids: list[str],
    protocol: str = "textworld",
    extra: Mapping[str, Any] | None = None,
) -> str:
    """Deterministic experiment id — same inputs ⇒ same id (scientific reproducibility)."""
    payload = {
        "lab_name": str(lab_name).strip().lower(),
        "seed": int(seed),
        "device_ids": sorted(str(d) for d in device_ids),
        "protocol": str(protocol).strip().lower(),
        "extra": dict(extra or {}),
        "format": "nexo-lab-exp-v1",
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"exp-{digest[:24]}"
