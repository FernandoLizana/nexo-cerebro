"""
Consolidación lenta: hipocampo → corteza (sueño NREM).

Durante el sueño, los recuerdos replayed refuerzan sinapsis corticales
(sensorial→límbico→asociativa) como memoria de largo plazo.
"""

from __future__ import annotations

import numpy as np

from .cortex import CorticalNetwork


def consolidate_to_cortex(
    cortex: CorticalNetwork,
    pattern: np.ndarray,
    *,
    valence: float = 0.0,
    strength: float = 1.0,
) -> dict:
    """
    Refuerzo lento de pesos en vías corticales según patrón hipocampal.
    Emociones fuertes (|valence| alto) aceleran consolidación.
    """
    p = np.asarray(pattern, dtype=np.float32).ravel()
    if p.size < cortex.n_sensory:
        p = np.pad(p, (0, cortex.n_sensory - p.size))
    p = p[: cortex.n_sensory]

    active_s = np.flatnonzero(p > 0.12)
    if active_s.size == 0:
        return {"edges_strengthened": 0, "delta_mean": 0.0}

    emotional = 0.6 + 0.4 * min(abs(valence), 1.0)
    delta_base = 0.012 * strength * emotional
    total_edges = 0
    deltas: list[float] = []

    layers = (
        (cortex.s_to_l, active_s, None),
        (cortex.l_to_a, None, None),
        (cortex.a_to_a, None, None),
    )

    # Sensorial → límbico (índices activos del patrón)
    syn = cortex.s_to_l
    for pre in active_s:
        if pre >= syn.n_pre:
            continue
        start, end = syn.indptr[pre], syn.indptr[pre + 1]
        if start == end:
            continue
        dw = delta_base * (0.5 + 0.5 * p[pre])
        syn.w[start:end] = np.clip(syn.w[start:end] + dw, -syn.w_max, syn.w_max)
        total_edges += end - start
        deltas.append(float(dw))
    syn._sync_csr_weights()

    # Límbico → asociativa (todas las filas con peso positivo, débil)
    for syn in (cortex.l_to_a, cortex.a_to_a):
        boost = delta_base * 0.65
        mask = syn.w > 0
        n = int(mask.sum())
        if n:
            syn.w[mask] = np.clip(syn.w[mask] + boost, -syn.w_max, syn.w_max)
            syn._sync_csr_weights()
            total_edges += n
            deltas.append(boost)

    return {
        "edges_strengthened": total_edges,
        "delta_mean": round(float(np.mean(deltas)) if deltas else 0.0, 5),
        "emotional_boost": round(emotional, 3),
    }


def forgetting_retention(*, age_hours: float, emotional: float = 0.0) -> float:
    """Curva de olvido temporal — emoción ralentiza decaimiento."""
    base = float(np.exp(-max(0.0, age_hours) / (48.0 + emotional * 72.0)))
    return float(np.clip(base, 0.15, 1.0))
