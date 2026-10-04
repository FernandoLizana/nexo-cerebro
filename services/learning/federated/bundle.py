"""Paper-ready reproducibility bundle for FL research runs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


BUNDLE_FORMAT = "nexo-fl-research-bundle-v1"

DISCLAIMER = (
    "Federated learning research artifact. Opt-in sandbox only. "
    "Not a production model deploy. Not a claim of validated cognition. "
    "Core IntegratedRuntime remains unchanged."
)


def build_reproducibility_bundle(
    *,
    seed: int,
    round_id: int,
    accepted: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    global_weights: Mapping[str, float],
    lora_delta: Mapping[str, float],
    eval_report: Mapping[str, Any],
    research_flag: Mapping[str, Any],
) -> dict[str, Any]:
    body = {
        "format_version": BUNDLE_FORMAT,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": int(seed),
        "round_id": int(round_id),
        "research_flag": dict(research_flag),
        "accepted_updates": list(accepted),
        "rejected_updates": list(rejected),
        "global_weights": {k: float(v) for k, v in global_weights.items()},
        "lora_delta": {k: float(v) for k, v in lora_delta.items()},
        "evaluation": dict(eval_report),
        "auto_deploy_to_core": False,
        "core_unchanged": True,
        "disclaimer": DISCLAIMER,
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    body["bundle_hash"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return body


def write_bundle(path: Path | str, bundle: Mapping[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(bundle), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
