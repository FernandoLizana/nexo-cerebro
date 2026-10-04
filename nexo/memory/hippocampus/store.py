"""Pattern separation y completion en hipocampo."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

import numpy as np

from nexo.memory.hippocampus.episode import EpisodicMemory


@dataclass
class HippocampalStore:
    capacity: int = 64
    separation_threshold: float = 0.92
    completion_noise: float = 0.06
    episodes: list[EpisodicMemory] = field(default_factory=list)

    def encode(self, episode: EpisodicMemory, *, rng: np.random.Generator) -> EpisodicMemory | None:
        """Pattern separation: rechaza/coloca aparte episodios demasiado similares."""
        cue = np.asarray(episode.cue_vector(), dtype=np.float64)
        for ep in self.episodes:
            existing = np.asarray(ep.cue_vector(), dtype=np.float64)
            if self._cosine(cue, existing) > self.separation_threshold:
                separated = np.asarray(episode.event_embedding, dtype=np.float64)
                separated = separated + rng.normal(0, 0.05, size=separated.shape)
                episode = EpisodicMemory(
                    episode_id=episode.episode_id,
                    event_embedding=tuple(float(x) for x in separated),
                    spatial_context=episode.spatial_context,
                    temporal_context=episode.temporal_context,
                    body_context=episode.body_context,
                    affective_context=episode.affective_context,
                    action=episode.action,
                    outcome=episode.outcome,
                    confidence=max(0.1, episode.confidence - 0.1),
                    source_identity=episode.source_identity,
                    tick=episode.tick,
                    modality=episode.modality,
                )
                break

        self.episodes.append(episode)
        if len(self.episodes) > self.capacity:
            self.episodes.pop(0)
        return episode

    def retrieve_partial(
        self,
        cue: tuple[float, ...],
        *,
        rng: np.random.Generator,
        top_k: int = 1,
    ) -> list[tuple[EpisodicMemory, float]]:
        """Pattern completion: reconstrucción imperfecta desde cue parcial."""
        if not self.episodes:
            return []
        c = np.asarray(cue, dtype=np.float64)
        scored: list[tuple[float, EpisodicMemory]] = []
        for ep in self.episodes:
            ec = np.asarray(ep.cue_vector(), dtype=np.float64)
            min_len = min(len(c), len(ec))
            sim = self._cosine(c[:min_len], ec[:min_len])
            scored.append((sim, ep))
        scored.sort(key=lambda x: -x[0])
        out: list[tuple[EpisodicMemory, float]] = []
        for sim, ep in scored[:top_k]:
            if sim < 0.25:
                continue
            recon_emb = np.asarray(ep.event_embedding, dtype=np.float64)
            recon_emb = recon_emb + rng.normal(0, self.completion_noise, size=recon_emb.shape)
            reconstructed = EpisodicMemory(
                episode_id=ep.episode_id,
                event_embedding=tuple(float(x) for x in recon_emb),
                spatial_context=ep.spatial_context,
                temporal_context=ep.temporal_context,
                body_context=ep.body_context,
                affective_context=ep.affective_context,
                action=ep.action,
                outcome=ep.outcome,
                confidence=ep.confidence * sim,
                source_identity=ep.source_identity,
                tick=ep.tick,
                modality=ep.modality,
            )
            out.append((reconstructed, sim))
        return out

    def sample_for_replay(
        self,
        *,
        rng: np.random.Generator,
        n: int = 1,
        min_confidence: float = 0.2,
    ) -> list[EpisodicMemory]:
        pool = [ep for ep in self.episodes if ep.confidence >= min_confidence]
        if not pool:
            return []
        n = min(n, len(pool))
        idx = rng.choice(len(pool), size=n, replace=False)
        return [pool[int(i)] for i in idx]

    def replace_episode(self, episode: EpisodicMemory) -> None:
        for i, ep in enumerate(self.episodes):
            if ep.episode_id == episode.episode_id:
                self.episodes[i] = episode
                return

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> float:
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na < 1e-9 or nb < 1e-9:
            return 0.0
        return float(np.dot(a, b) / (na * nb))
