"""Event ingestion — validate NEXO events; no auto-promotion to global truth."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Mapping

from protocols.events.codec import decode_event


@dataclass
class IngestedEvent:
    received_at: float
    source_node_id: str
    event: dict[str, Any]
    quarantined: bool = True  # S7/S9: always quarantine until later pipeline

    def to_dict(self) -> dict[str, Any]:
        return {
            "received_at": self.received_at,
            "source_node_id": self.source_node_id,
            "quarantined": self.quarantined,
            "event": dict(self.event),
        }


class EventIngestor:
    def __init__(self) -> None:
        self._events: list[IngestedEvent] = []

    def ingest(self, *, source_node_id: str, event: Mapping[str, Any]) -> IngestedEvent:
        decoded = decode_event(event)
        item = IngestedEvent(
            received_at=time.time(),
            source_node_id=source_node_id,
            event=decoded.to_dict(),
            quarantined=True,
        )
        self._events.append(item)
        return item

    def list_quarantine(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._events[-limit:]]
