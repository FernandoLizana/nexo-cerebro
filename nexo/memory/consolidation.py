"""Consolidación mnésica hipocampo → trazas de largo plazo."""

from __future__ import annotations

from dataclasses import dataclass

from nexo.memory.hippocampus.episode import EpisodicMemory


@dataclass
class MemoryConsolidator:
    """Refuerzo de confianza episódica y transferencia simbólica."""

    consolidated_ids: set[str]

    def __init__(self) -> None:
        self.consolidated_ids = set()

    def consolidate(self, episode: EpisodicMemory) -> EpisodicMemory:
        if episode.episode_id in self.consolidated_ids:
            return episode
        self.consolidated_ids.add(episode.episode_id)
        return EpisodicMemory(
            episode_id=episode.episode_id,
            event_embedding=episode.event_embedding,
            spatial_context=episode.spatial_context,
            temporal_context=episode.temporal_context,
            body_context=episode.body_context,
            affective_context=episode.affective_context,
            action=episode.action,
            outcome=episode.outcome,
            confidence=min(0.98, episode.confidence + 0.15),
            source_identity=episode.source_identity,
            tick=episode.tick,
            modality=episode.modality,
        )
