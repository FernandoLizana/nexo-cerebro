"""
Telemetría cognitiva compacta por tick (Level 2.2).

No selecciona acciones: solo registra estado serializable para API/Arena/HUD.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class NeuralTelemetry:
    capacity: int = 256
    buffer: deque = field(default_factory=lambda: deque(maxlen=256))
    tick_count: int = 0

    def __post_init__(self) -> None:
        self.buffer = deque(maxlen=max(8, int(self.capacity)))

    def record_from_tick(self, payload: dict[str, Any], *, tick: int | None = None) -> dict[str, Any]:
        delib = payload.get("deliberation") or {}
        drives = payload.get("drives") or {}
        top_drive = ""
        if drives:
            top_drive = max(drives.items(), key=lambda item: float(item[1]))[0]
        aff = payload.get("affordance_map") or {}
        row = {
            "tick": int(tick if tick is not None else self.tick_count),
            "top_drive": top_drive,
            "choice_key": str(delib.get("choice_key") or ""),
            "agency": float(delib.get("agency") or 0.0),
            "conflict": float(delib.get("conflict") or 0.0),
            "inhibited": bool(delib.get("inhibited")),
            "room": str((payload.get("world") or {}).get("room") or ""),
            "affordance_biases": dict(aff.get("last_biases") or {}),
            "affordance_records": int(aff.get("record_count") or 0),
            "last_observation": aff.get("last_observation"),
            "events": [
                {"type": e.get("type"), "object_type": e.get("object_type"), "target": e.get("target")}
                for e in (payload.get("events") or [])[:6]
                if isinstance(e, dict)
            ],
            "agency_guard": payload.get("agency_guard")
            or {
                "affordances_select_actions": False,
                "deliberation_selects_actions": True,
            },
        }
        self.buffer.append(row)
        self.tick_count += 1
        return row

    def latest(self) -> dict[str, Any] | None:
        return dict(self.buffer[-1]) if self.buffer else None

    def recent(self, n: int = 16) -> list[dict[str, Any]]:
        items = list(self.buffer)[-max(1, n) :]
        return [dict(x) for x in items]

    def clear(self) -> None:
        self.buffer.clear()
        self.tick_count = 0

    def export_jsonl(self, path: Path) -> int:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            for row in self.buffer:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return len(self.buffer)

    def to_dict(self) -> dict[str, Any]:
        latest = self.latest()
        return {
            "tick_count": self.tick_count,
            "buffer_size": len(self.buffer),
            "capacity": self.buffer.maxlen,
            "latest": latest,
            "recent": self.recent(8),
            "agency_note": "Telemetry is observational; PFC remains the sole choice_key writer",
        }
