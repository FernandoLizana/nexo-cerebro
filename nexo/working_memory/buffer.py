"""Buffer de memoria de trabajo con capacidad limitada e interferencia."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from nexo.working_memory.item import WorkingMemoryItem


@dataclass
class WorkingMemoryBuffer:
    capacity: int = 4
    decay_rate: float = 0.04
    interference_strength: float = 0.08
    items: list[WorkingMemoryItem] = field(default_factory=list)

    def gate_in(self, key: str, *, embedding: tuple[float, ...], tick: int, priority: float = 1.0) -> None:
        for i, item in enumerate(self.items):
            if item.key == key:
                self.items[i] = WorkingMemoryItem(
                    key=key,
                    activation=min(1.0, item.activation + 0.25 * priority),
                    embedding=embedding or item.embedding,
                    tick_added=tick,
                    protected=item.protected,
                )
                self._apply_interference(key, embedding)
                self._enforce_capacity()
                return
        self.items.append(
            WorkingMemoryItem(
                key=key,
                activation=0.55 * priority,
                embedding=embedding,
                tick_added=tick,
            )
        )
        self._apply_interference(key, embedding)
        self._enforce_capacity()

    def _apply_interference(self, key: str, embedding: tuple[float, ...]) -> None:
        if not embedding:
            return
        vec = np.asarray(embedding, dtype=np.float64)
        for i, item in enumerate(self.items):
            if item.key == key or not item.embedding:
                continue
            sim = self._cosine(vec, np.asarray(item.embedding))
            if sim > 0.85:
                self.items[i] = WorkingMemoryItem(
                    key=item.key,
                    activation=max(0.0, item.activation - self.interference_strength),
                    embedding=item.embedding,
                    tick_added=item.tick_added,
                )

    def tick_decay(self, tick: int) -> None:
        self.items = [it.decay(self.decay_rate) for it in self.items if it.activation > 0.04]
        if self.items:
            recency_boost = max(self.items, key=lambda x: x.tick_added)
            idx = self.items.index(recency_boost)
            self.items[idx] = WorkingMemoryItem(
                key=recency_boost.key,
                activation=min(1.0, recency_boost.activation + 0.03),
                embedding=recency_boost.embedding,
                tick_added=recency_boost.tick_added,
            )

    def _enforce_capacity(self) -> None:
        if len(self.items) <= self.capacity:
            return
        self.items.sort(key=lambda x: -x.activation)
        self.items = self.items[: self.capacity]

    def to_tuples(self) -> list[tuple[str, float]]:
        return [(it.key, it.activation) for it in self.items]

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na < 1e-9 or nb < 1e-9:
            return 0.0
        return float(np.dot(a, b) / (na * nb))
