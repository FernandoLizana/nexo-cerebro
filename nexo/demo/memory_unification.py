"""Promoción episodios integrados → memoria legacy SQLite (Fase 14)."""

from __future__ import annotations

from typing import Any

import numpy as np

PROMOTION_MIN_CONFIDENCE = 0.35


def _episode_to_pattern(episode: Any, dim: int) -> np.ndarray:
    emb = np.asarray(episode.event_embedding, dtype=np.float32).ravel()
    if emb.size < dim:
        emb = np.pad(emb, (0, dim - emb.size))
    return emb[:dim]


def promote_episode_to_legacy(brain: Any, episode: Any) -> dict[str, Any]:
    """Tras consolidación sueño: episodio hippo → SQLite legacy."""
    if brain is None or episode is None:
        return {"promoted": False, "reason": "missing_brain_or_episode"}
    if float(getattr(episode, "confidence", 0.0)) < PROMOTION_MIN_CONFIDENCE:
        return {"promoted": False, "reason": "low_confidence"}

    store = getattr(brain, "memory_store", None)
    if store is None:
        return {"promoted": False, "reason": "no_memory_store"}

    aff = getattr(episode, "affective_context", (0.0, 0.0, 0.0)) or (0.0, 0.0, 0.0)
    valence = float(aff[0]) if len(aff) > 0 else 0.0
    arousal = float(aff[1]) if len(aff) > 1 else 0.3
    action = str(getattr(episode, "action", "") or "episode")
    label = f"{action}@{getattr(episode, 'outcome', 'consolidated')}"[:80]
    key = f"hippo_{getattr(episode, 'episode_id', 'unknown')}"
    pattern_dim = int(getattr(store, "pattern_dim", len(episode.event_embedding)))
    pattern = _episode_to_pattern(episode, pattern_dim)

    body = {}
    bc = getattr(episode, "body_context", ()) or ()
    if len(bc) >= 3:
        body = {"energy": float(bc[0]), "fatigue": float(bc[1]), "pain": float(bc[2])}

    store.store(
        key,
        pattern,
        label=label,
        modality=str(getattr(episode, "modality", "") or "world"),
        motor=[4],
        valence=valence,
        arousal=arousal,
        tags=["hippocampal", "unified", action],
        body=body,
        room="integrated",
    )
    return {
        "promoted": True,
        "key": key,
        "episode_id": getattr(episode, "episode_id", ""),
        "confidence": float(getattr(episode, "confidence", 0.0)),
    }
