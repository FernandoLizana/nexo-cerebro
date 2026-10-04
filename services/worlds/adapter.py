"""Abstract WorldAdapter interface (S5+)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class WorldSpec:
    world_type: str
    seed: int
    version: str = "1"


@runtime_checkable
class WorldAdapter(Protocol):
    """Minimal multi-Being world surface for Swarm experiments."""

    @property
    def spec(self) -> WorldSpec:
        ...

    def reset(self, seed: int | None = None) -> None:
        ...

    def place_being(self, being_id: str, place: str | None = None) -> str:
        ...

    def tick(self) -> list[dict[str, Any]]:
        """Advance one world step; return emitted events."""
        ...

    def snapshot(self) -> dict[str, Any]:
        ...
