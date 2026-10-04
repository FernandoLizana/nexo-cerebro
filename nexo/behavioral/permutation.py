"""Prueba de permutación para deltas vs baseline."""

from __future__ import annotations

import numpy as np


def permutation_p_value(
    baseline: list[float],
    candidate: list[float],
    *,
    n_perm: int = 1000,
    seed: int = 0,
) -> float:
    """p-value aproximado two-sided para diferencia de medias."""
    if not baseline or not candidate:
        return 1.0
    if len(baseline) < 2 and len(candidate) < 2:
        return 1.0 if baseline == candidate else 0.5
    rng = np.random.default_rng(seed)
    base = np.asarray(baseline, dtype=np.float64)
    cand = np.asarray(candidate, dtype=np.float64)
    observed = abs(float(np.mean(cand)) - float(np.mean(base)))
    pooled = np.concatenate([base, cand])
    n_base = len(base)
    count = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        perm_base = pooled[:n_base]
        perm_cand = pooled[n_base:]
        perm_delta = abs(float(np.mean(perm_cand)) - float(np.mean(perm_base)))
        if perm_delta >= observed - 1e-12:
            count += 1
    return (count + 1) / (n_perm + 1)
