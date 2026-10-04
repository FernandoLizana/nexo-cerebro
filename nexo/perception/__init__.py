"""Percepción predictiva — jerarquía, error y precisión."""

from __future__ import annotations

from nexo.perception.hierarchy import PredictiveHierarchy, PredictionResult
from nexo.perception.prediction_error import compute_surprise, weighted_prediction_error
from nexo.perception.precision_weighting import PrecisionEstimator

__all__ = [
    "PredictiveHierarchy",
    "PredictionResult",
    "PrecisionEstimator",
    "compute_surprise",
    "weighted_prediction_error",
]
