"""Ítems de memoria de trabajo."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkingMemoryItem:
    key: str
    activation: float
    embedding: tuple[float, ...] = ()
    tick_added: int = 0
    protected: bool = False

    def decay(self, rate: float) -> WorkingMemoryItem:
        if self.protected:
            return self
        return WorkingMemoryItem(
            key=self.key,
            activation=max(0.0, self.activation - rate),
            embedding=self.embedding,
            tick_added=self.tick_added,
            protected=self.protected,
        )
