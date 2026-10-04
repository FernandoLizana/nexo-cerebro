"""Corrección múltiple sobre p-values de permutación."""

from __future__ import annotations

from typing import Any


def benjamini_hochberg_fdr(p_values: list[float]) -> list[float]:
    """Ajuste FDR Benjamini-Hochberg; devuelve q-values en el mismo orden."""
    if not p_values:
        return []
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    q_values = [1.0] * n
    prev_q = 1.0
    for rank, (idx, p) in enumerate(reversed(indexed), start=1):
        i = n - rank
        q = min(prev_q, p * n / (i + 1))
        q_values[idx] = q
        prev_q = q
    return q_values


def apply_fdr_to_effects(effect_sizes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Añade permutation_q a entradas con permutation_p."""
    with_p = [(i, e) for i, e in enumerate(effect_sizes) if "permutation_p" in e]
    if not with_p:
        return effect_sizes
    q_vals = benjamini_hochberg_fdr([float(e["permutation_p"]) for _, e in with_p])
    out = [dict(e) for e in effect_sizes]
    for (idx, _), q in zip(with_p, q_vals):
        out[idx]["permutation_q"] = round(q, 6)
        out[idx]["significant_fdr_05"] = q < 0.05
    return out
