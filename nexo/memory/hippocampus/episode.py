"""Episodio mnésico reconstructivo."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EpisodicMemory:
    episode_id: str
    event_embedding: tuple[float, ...]
    spatial_context: tuple[float, ...]
    temporal_context: tuple[float, ...]
    body_context: tuple[float, ...]
    affective_context: tuple[float, ...]
    action: str | None
    outcome: str | None
    confidence: float
    source_identity: str | None
    tick: int
    modality: str = ""

    def cue_vector(self) -> tuple[float, ...]:
        return self.event_embedding + self.spatial_context[:2] + self.temporal_context[:1]
