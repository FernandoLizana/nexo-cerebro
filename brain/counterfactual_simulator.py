"""
Simulador contrafactual acotado (Level 2.3).

Predice consecuencias aproximadas de candidatos PFC sin modificar el mundo
ni escribir choice_key. Solo aporta bias Go limitado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .affordance_map import AFFORDANCE_BIAS_MAX, DRIVE_GAIN_FIELD, HOMEOSTATIC_FIELDS

COUNTERFACTUAL_BIAS_MAX = 0.06
SCHEMA_HEURISTICS: dict[str, dict[str, float]] = {
    "drink": {"thirst": -0.4, "pleasure": 0.05},
    "eat": {"hunger": -0.4, "thirst": -0.08, "pleasure": 0.05},
    "eat_cooked": {"hunger": -0.45, "pleasure": 0.08},
    "rest": {"fatigue": -0.3, "comfort": 0.08},
    "sleep": {"fatigue": -0.45, "comfort": 0.1},
    "hygiene": {"hygiene": -0.4, "comfort": 0.06},
    "bathroom": {"bladder": -0.5, "comfort": 0.05},
    "harvest": {"comfort": 0.04, "pleasure": 0.03},
    "wander": {},
}


@dataclass
class CounterfactualPrediction:
    candidate_key: str
    expected_outcomes: dict[str, float]
    expected_homeostasis_gain: float
    confidence: float
    source: str  # affordance | heuristic
    bias: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_key": self.candidate_key,
            "expected_outcomes": {
                k: round(float(v), 4) for k, v in self.expected_outcomes.items()
            },
            "expected_homeostasis_gain": round(self.expected_homeostasis_gain, 4),
            "confidence": round(self.confidence, 4),
            "source": self.source,
            "bias": round(self.bias, 4),
        }


@dataclass
class CounterfactualSimulator:
    last_predictions: list[CounterfactualPrediction] = field(default_factory=list)
    last_biases: dict[str, float] = field(default_factory=dict)

    def _gain(self, outcomes: dict[str, float], dominant_drive: str) -> float:
        field_sign = DRIVE_GAIN_FIELD.get(dominant_drive)
        if field_sign:
            name, sign = field_sign
            return float(sign * outcomes.get(name, 0.0))
        return float(
            -0.2 * outcomes.get("hunger", 0.0)
            - 0.2 * outcomes.get("thirst", 0.0)
            - 0.15 * outcomes.get("fatigue", 0.0)
            + 0.05 * outcomes.get("comfort", 0.0)
        )

    def predict_for(
        self,
        *,
        candidate_keys: list[str],
        dominant_drive: str,
        room: str,
        affordance_map=None,
    ) -> list[CounterfactualPrediction]:
        preds: list[CounterfactualPrediction] = []
        aff_records = list(getattr(affordance_map, "records", {}).values()) if affordance_map else []
        for key in candidate_keys:
            source = "heuristic"
            confidence = 0.22
            outcomes = {
                name: float(SCHEMA_HEURISTICS.get(key, {}).get(name, 0.0))
                for name in HOMEOSTATIC_FIELDS
            }
            # Prefer learned affordance means when available for this candidate.
            matches = [
                r
                for r in aff_records
                if r.candidate_key == key
                and (not dominant_drive or r.dominant_drive == dominant_drive)
            ]
            if matches:
                best = max(matches, key=lambda r: r.confidence)
                if best.confidence >= 0.12 and best.observation_count > 0:
                    outcomes = {
                        name: float(best.expected_outcomes.get(name, 0.0))
                        for name in HOMEOSTATIC_FIELDS
                    }
                    confidence = float(best.confidence)
                    source = "affordance"
            gain = self._gain(outcomes, dominant_drive)
            # Uncertainty attenuates bias (no inventar certeza).
            raw = gain * confidence * 0.85
            if source == "heuristic":
                raw *= 0.45
            if room and source == "affordance":
                # leve bonus contextual ya incorporado en affordance; no multiplicar de más
                pass
            bias = float(max(-COUNTERFACTUAL_BIAS_MAX, min(COUNTERFACTUAL_BIAS_MAX, raw)))
            # Nunca superar el techo de affordance global.
            bias = float(max(-AFFORDANCE_BIAS_MAX, min(AFFORDANCE_BIAS_MAX, bias)))
            preds.append(
                CounterfactualPrediction(
                    candidate_key=key,
                    expected_outcomes=outcomes,
                    expected_homeostasis_gain=gain,
                    confidence=confidence,
                    source=source,
                    bias=bias,
                )
            )
        self.last_predictions = sorted(
            preds, key=lambda p: abs(p.bias), reverse=True
        )
        self.last_biases = {
            p.candidate_key: p.bias for p in self.last_predictions if abs(p.bias) > 1e-6
        }
        return self.last_predictions

    def biases_for(
        self,
        *,
        candidate_keys: list[str],
        dominant_drive: str,
        room: str,
        affordance_map=None,
    ) -> dict[str, float]:
        self.predict_for(
            candidate_keys=candidate_keys,
            dominant_drive=dominant_drive,
            room=room,
            affordance_map=affordance_map,
        )
        return dict(self.last_biases)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bias_max": COUNTERFACTUAL_BIAS_MAX,
            "last_biases": {k: round(v, 4) for k, v in self.last_biases.items()},
            "predictions": [p.to_dict() for p in self.last_predictions[:8]],
            "agency_note": "Counterfactuals predict only; PFC selects choice_key",
        }
