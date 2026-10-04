"""Error de predicción ponderado por precisión."""

from __future__ import annotations

import numpy as np


def weighted_prediction_error(
    observation: np.ndarray,
    prediction: np.ndarray,
    precision: float,
) -> np.ndarray:
    """Aproximación: error = precision * (obs - pred)."""
    return float(precision) * (np.asarray(observation, dtype=np.float64) - np.asarray(prediction, dtype=np.float64))


def compute_surprise(error: np.ndarray) -> float:
    """Magnitud del error como proxy de sorpresa (no Bayes exacto)."""
    return float(np.sqrt(np.mean(np.square(error))))
