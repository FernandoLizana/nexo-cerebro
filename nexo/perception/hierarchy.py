"""Jerarquía predictiva multilevel — aproximación funcional."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from nexo.perception.prediction_error import compute_surprise, weighted_prediction_error


@dataclass(frozen=True)
class PredictionResult:
    modality: str
    observation: tuple[float, ...]
    prediction: tuple[float, ...]
    posterior: tuple[float, ...]
    error: tuple[float, ...]
    surprise: float
    precision: float
    level: str


@dataclass
class PredictiveLevel:
    name: str
    learning_rate: float = 0.15
    _state: dict[str, np.ndarray] = field(default_factory=dict)

    def prior(self, modality: str, dim: int) -> np.ndarray:
        if modality not in self._state:
            self._state[modality] = np.zeros(dim, dtype=np.float64)
        return self._state[modality].copy()

    def update(self, modality: str, posterior: np.ndarray) -> None:
        self._state[modality] = np.asarray(posterior, dtype=np.float64).copy()


@dataclass
class PredictiveHierarchy:
    """Niveles: sensory → features → scene (aproximación compacta)."""

    sensory: PredictiveLevel = field(default_factory=lambda: PredictiveLevel("sensory", 0.25))
    features: PredictiveLevel = field(default_factory=lambda: PredictiveLevel("features", 0.12))
    scene: PredictiveLevel = field(default_factory=lambda: PredictiveLevel("scene", 0.08))
    habituation: dict[str, float] = field(default_factory=dict)
    habituation_decay: float = 0.92

    def update(
        self,
        *,
        modality: str,
        observation: np.ndarray,
        precision: float,
    ) -> PredictionResult:
        obs = np.asarray(observation, dtype=np.float64)
        dim = obs.shape[0]

        pred_s = self.sensory.prior(modality, dim)
        err_s = weighted_prediction_error(obs, pred_s, precision)
        post_s = pred_s + self.sensory.learning_rate * err_s

        pred_f = self.features.prior(modality, dim)
        err_f = weighted_prediction_error(post_s, pred_f, precision * 0.8)
        post_f = pred_f + self.features.learning_rate * err_f

        pred_sc = self.scene.prior(modality, dim)
        err_sc = weighted_prediction_error(post_f, pred_sc, precision * 0.6)
        post_sc = pred_sc + self.scene.learning_rate * err_sc

        self.sensory.update(modality, post_s)
        self.features.update(modality, post_f)
        self.scene.update(modality, post_sc)

        surprise = compute_surprise(err_s)
        hab = self.habituation.get(modality, 0.0)
        surprise_adj = surprise * (1.0 - hab * 0.5)
        self.habituation[modality] = hab * self.habituation_decay + surprise * 0.1

        return PredictionResult(
            modality=modality,
            observation=tuple(float(x) for x in obs),
            prediction=tuple(float(x) for x in pred_s),
            posterior=tuple(float(x) for x in post_sc),
            error=tuple(float(x) for x in err_s),
            surprise=surprise_adj,
            precision=precision,
            level="scene",
        )
