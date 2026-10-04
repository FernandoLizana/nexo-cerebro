"""Privacy — pseudonymization, redaction, participant deletion."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SECRET_PATTERNS = (
    re.compile(r"password\s*[:=]\s*\S+", re.I),
    re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
)


def pseudonymize_participant_id(raw_id: str, *, study_salt: str) -> str:
    digest = hashlib.sha256(f"{study_salt}|{raw_id}".encode()).hexdigest()
    return f"participant-{digest[:12]}"


def redact_secrets(text: str) -> str:
    out = text
    for pat in SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def redact_event_dict(data: dict[str, Any]) -> dict[str, Any]:
    blob = redact_secrets(json.dumps(data, default=str))
    return json.loads(blob)


def delete_participant(participant_id: str, study_root: Path | str) -> dict[str, Any]:
    """Remove participant raw events and summaries from study artifacts."""
    root = Path(study_root)
    removed: list[str] = []
    for path in root.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict) and data.get("participant_id") == participant_id:
            path.unlink(missing_ok=True)
            removed.append(str(path))
        elif isinstance(data, list):
            filtered = [r for r in data if r.get("participant_id") != participant_id]
            if len(filtered) != len(data):
                path.write_text(json.dumps(filtered, indent=2), encoding="utf-8")
                removed.append(str(path))
    index = root / "participant_index.json"
    if index.exists():
        idx = json.loads(index.read_text(encoding="utf-8"))
        if participant_id in idx:
            del idx[participant_id]
            index.write_text(json.dumps(idx, indent=2), encoding="utf-8")
    return {"participant_id": participant_id, "removed_paths": removed, "deleted": True}
