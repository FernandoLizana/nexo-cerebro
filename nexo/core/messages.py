"""Mensajes retrasados entre procesos cognitivos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CognitiveMessage:
    source: str
    target: str
    signal_type: str
    payload: dict[str, Any]
    deliver_at_tick: int
    trace_id: str = ""


@dataclass
class MessageBus:
    """Cola de mensajes con latencia en ticks."""

    _pending: list[CognitiveMessage] = field(default_factory=list)

    def send(self, msg: CognitiveMessage) -> None:
        self._pending.append(msg)

    def deliver(self, tick: int) -> list[CognitiveMessage]:
        ready = [m for m in self._pending if m.deliver_at_tick <= tick]
        self._pending = [m for m in self._pending if m.deliver_at_tick > tick]
        return ready

    def pending_count(self) -> int:
        return len(self._pending)
