"""Simulation event types — local queue only (no network transport)."""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SimEventKind(str, Enum):
    HEARTBEAT = "HEARTBEAT"
    INTERACT = "INTERACT"
    BROADCAST = "BROADCAST"
    TICK = "TICK"
    KNOWLEDGE_GOSSIP = "KNOWLEDGE_GOSSIP"


_seq = itertools.count(1)


@dataclass(order=True)
class SimEvent:
    """Priority-queue item: earlier ``time`` first; stable ``seq`` tie-break."""

    time: float
    seq: int = field(compare=True, default_factory=lambda: next(_seq))
    kind: SimEventKind = field(compare=False, default=SimEventKind.TICK)
    source_id: str = field(compare=False, default="")
    target_id: str | None = field(compare=False, default=None)
    payload: dict[str, Any] = field(compare=False, default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "time": self.time,
            "seq": self.seq,
            "kind": self.kind.value,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "payload": dict(self.payload),
        }
