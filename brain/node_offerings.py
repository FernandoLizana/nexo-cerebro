"""Unread material left on nodes. The central takes one only when it chooses.

Does not open sockets and does not change the 3D house.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

def _shelf() -> Path:
    override = os.environ.get("NEXO_NODE_SHELF", "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "data" / "node_shelf"
_LOCK = threading.Lock()


def unread_offerings() -> list[dict[str, Any]]:
    shelf = _shelf()
    if not shelf.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(shelf.glob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if row.get("status") == "held":
            rows.append(row)
    return rows


def peek_offering() -> dict[str, Any] | None:
    rows = unread_offerings()
    return rows[0] if rows else None


def take_offering(offering_id: str | None = None) -> dict[str, Any] | None:
    """Mark one held item as taken and return its text. None if the shelf is empty."""
    with _LOCK:
        chosen = None
        path = None
        shelf = _shelf()
        for candidate in sorted(shelf.glob("*.json")) if shelf.exists() else []:
            try:
                row = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if row.get("status") != "held":
                continue
            if offering_id and row.get("id") != offering_id:
                continue
            chosen = row
            path = candidate
            break
        if chosen is None or path is None:
            return None
        text_path = shelf / f"{chosen['id']}.txt"
        try:
            text = text_path.read_text(encoding="utf-8")
        except OSError:
            text = str(chosen.get("note") or "")
        chosen["status"] = "taken"
        chosen["taken_at"] = int(time.time())
        path.write_text(json.dumps(chosen), encoding="utf-8")
        chosen["text"] = text
        return chosen
