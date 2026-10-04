"""Statistics for calibration — correlation, Brier, ECE, bootstrap CI."""

from __future__ import annotations

import math
import random
from typing import Any


def pearson_correlation(xs: list[float], ys: list[float]) -> float | None:
    n = min(len(xs), len(ys))
    if n < 3:
        return None
    xs, ys = xs[:n], ys[:n]
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return None if den == 0 else round(num / den, 4)


def spearman_correlation(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3:
        return None

    def ranks(vals: list[float]) -> list[float]:
        ordered = sorted((v, i) for i, v in enumerate(vals))
        out = [0.0] * len(vals)
        for r, (_, i) in enumerate(ordered, 1):
            out[i] = float(r)
        return out

    return pearson_correlation(ranks(xs), ranks(ys))


def brier_score(probs: list[float], outcomes: list[int]) -> float | None:
    if not probs or len(probs) != len(outcomes):
        return None
    return round(sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / len(probs), 4)


def expected_calibration_error(probs: list[float], outcomes: list[int], *, bins: int = 10) -> float | None:
    if not probs or len(probs) != len(outcomes):
        return None
    bucket: dict[int, list[tuple[float, int]]] = {i: [] for i in range(bins)}
    for p, o in zip(probs, outcomes):
        idx = min(bins - 1, int(p * bins))
        bucket[idx].append((p, o))
    total = len(probs)
    ece = 0.0
    for items in bucket.values():
        if not items:
            continue
        avg_p = sum(x[0] for x in items) / len(items)
        avg_o = sum(x[1] for x in items) / len(items)
        ece += (len(items) / total) * abs(avg_p - avg_o)
    return round(ece, 4)


def bootstrap_ci(
    xs: list[float],
    ys: list[float],
    *,
    stat_fn=pearson_correlation,
    n_boot: int = 200,
    seed: int = 42,
) -> dict[str, Any]:
    rng = random.Random(seed)
    n = min(len(xs), len(ys))
    if n < 3:
        return {"estimate": None, "ci_low": None, "ci_high": None, "n": n}
    stats: list[float] = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        val = stat_fn([xs[i] for i in idx], [ys[i] for i in idx])
        if val is not None:
            stats.append(val)
    if not stats:
        return {"estimate": None, "ci_low": None, "ci_high": None, "n": n}
    stats.sort()
    return {
        "estimate": stat_fn(xs[:n], ys[:n]),
        "ci_low": round(stats[int(0.025 * len(stats))], 4),
        "ci_high": round(stats[int(0.975 * len(stats))], 4),
        "n": n,
    }
