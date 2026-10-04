"""Lightweight logical node — not an OS process."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogicalNode:
    """In-process stand-in for a voluntary NEXO node."""

    node_id: str
    beings: list[str] = field(default_factory=list)
    neighbors: list[str] = field(default_factory=list)
    heartbeats: int = 0
    interactions: int = 0
    inbox_size: int = 0
    props: dict[str, Any] = field(default_factory=dict)

    def estimate_bytes(self) -> int:
        # Rough scientific budget accounting (not OS RSS).
        base = 256
        base += 32 * len(self.beings)
        base += 24 * len(self.neighbors)
        base += 64 * max(0, self.inbox_size)
        return base

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "beings": list(self.beings),
            "neighbors": list(self.neighbors),
            "heartbeats": self.heartbeats,
            "interactions": self.interactions,
            "inbox_size": self.inbox_size,
        }
