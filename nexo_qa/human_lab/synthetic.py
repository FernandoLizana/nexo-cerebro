"""Synthetic pipeline fixtures — NOT human validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests" / "fixtures" / "human_lab"

SYNTHETIC_LABEL = "SYNTHETIC_PIPELINE_TEST"
NOT_HUMAN_VALIDATION = "NOT HUMAN VALIDATION"


def load_synthetic_runs(name: str = "synthetic_runs.json") -> list[dict[str, Any]]:
    path = FIXTURES / name
    data = json.loads(path.read_text(encoding="utf-8"))
    runs = data.get("runs") or data
    for r in runs:
        r["synthetic"] = True
    return runs


def load_synthetic_events(name: str = "synthetic_events.json") -> list[dict[str, Any]]:
    path = FIXTURES / name
    data = json.loads(path.read_text(encoding="utf-8"))
    events = data.get("events") or data
    for e in events:
        e.setdefault("metadata", {})["pipeline_label"] = SYNTHETIC_LABEL
    return events


def load_synthetic_nexo_summaries(name: str = "synthetic_nexo_summaries.json") -> list[dict[str, Any]]:
    path = FIXTURES / name
    data = json.loads(path.read_text(encoding="utf-8"))
    summaries = data.get("summaries") or data
    for s in summaries:
        s["synthetic"] = True
    return summaries


def synthetic_disclaimer() -> dict[str, str]:
    return {
        "label": SYNTHETIC_LABEL,
        "warning": NOT_HUMAN_VALIDATION,
    }
