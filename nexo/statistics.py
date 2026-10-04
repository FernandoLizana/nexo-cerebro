"""Estadística descriptiva multi-seed con advertencias metodológicas."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class SeedSummary:
    n_total: int
    n_valid: int
    n_nan: int
    n_failed: int
    mean: float
    median: float
    std: float
    minimum: float
    maximum: float
    p25: float
    p75: float
    ci95_low: float
    ci95_high: float
    mean_difference: float | None = None
    cohens_d: float | None = None
    hedges_g: float | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_total": self.n_total,
            "n_valid": self.n_valid,
            "n_nan": self.n_nan,
            "n_failed": self.n_failed,
            "mean": self.mean,
            "median": self.median,
            "std": self.std,
            "min": self.minimum,
            "max": self.maximum,
            "p25": self.p25,
            "p75": self.p75,
            "ci95_low": self.ci95_low,
            "ci95_high": self.ci95_high,
            "mean_difference": self.mean_difference,
            "cohens_d": self.cohens_d,
            "hedges_g": self.hedges_g,
            "warnings": list(self.warnings),
        }


def _clean(values: list[float]) -> tuple[np.ndarray, list[str]]:
    warnings: list[str] = []
    arr = np.asarray(values, dtype=np.float64)
    n_total = int(arr.size)
    n_nan = int(np.isnan(arr).sum())
    if n_nan:
        warnings.append("nan_values_filtered")
    valid = arr[~np.isnan(arr)]
    n_valid = int(valid.size)
    n_failed = n_total - n_valid
    return valid, warnings


def _cohens_d(sample: np.ndarray, baseline: float) -> float:
    if sample.size < 2:
        return math.nan
    std = float(np.std(sample, ddof=1))
    if std < 1e-12:
        return math.nan
    return (float(np.mean(sample)) - baseline) / std


def _hedges_g(sample: np.ndarray, baseline: float) -> float:
    n = sample.size
    if n < 2:
        return math.nan
    d = _cohens_d(sample, baseline)
    if math.isnan(d):
        return math.nan
    correction = 1.0 - 3.0 / (4.0 * n - 1.0)
    return d * correction


def summarize_values(values: list[float], *, baseline: float | None = None) -> SeedSummary:
    arr, warnings = _clean(values)
    n_total = len(values)
    n_valid = int(arr.size)
    n_nan = n_total - n_valid
    if n_valid == 0:
        return SeedSummary(
            n_total, 0, n_nan, n_total, math.nan, math.nan, math.nan, math.nan, math.nan,
            math.nan, math.nan, math.nan, math.nan, warnings=["empty_sample"],
        )
    if n_valid == 1:
        warnings.append("single_seed")
    if n_valid > 1 and np.all(arr == arr[0]):
        warnings.append("constant_across_seeds")
    std = float(np.std(arr, ddof=1)) if n_valid > 1 else 0.0
    mean = float(np.mean(arr))
    se = std / math.sqrt(n_valid) if n_valid > 1 else 0.0
    # CI aproximado t≈1.96 para n>=30; documentado como normal aprox
    ci_low = mean - 1.96 * se
    ci_high = mean + 1.96 * se
    md = (mean - baseline) if baseline is not None else None
    cd = _cohens_d(arr, baseline) if baseline is not None else None
    hg = _hedges_g(arr, baseline) if baseline is not None else None
    return SeedSummary(
        n_total=n_total,
        n_valid=n_valid,
        n_nan=n_nan,
        n_failed=0,
        mean=mean,
        median=float(np.median(arr)),
        std=std,
        minimum=float(np.min(arr)),
        maximum=float(np.max(arr)),
        p25=float(np.percentile(arr, 25)),
        p75=float(np.percentile(arr, 75)),
        ci95_low=ci_low,
        ci95_high=ci_high,
        mean_difference=md,
        cohens_d=cd,
        hedges_g=hg,
        warnings=warnings,
    )
