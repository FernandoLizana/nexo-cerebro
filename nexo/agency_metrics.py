"""Métricas compuestas de agency (proxies computacionales, no libre albedrío)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


@dataclass(frozen=True)
class AgencyMetrics:
    """Proxies separados; legacy_agency_score conserva compatibilidad histórica."""

    legacy_agency_score: float
    decision_margin: float
    confidence_from_margin: float
    top_down_contribution: float
    impulse_override_rate: float
    pfc_limbic_conflict: float
    veto_success_rate: float
    action_entropy: float

    def to_dict(self) -> dict[str, float]:
        return {
            "legacy_agency_score": self.legacy_agency_score,
            "decision_margin": self.decision_margin,
            "confidence_from_margin": self.confidence_from_margin,
            "top_down_contribution": self.top_down_contribution,
            "impulse_override_rate": self.impulse_override_rate,
            "pfc_limbic_conflict": self.pfc_limbic_conflict,
            "veto_success_rate": self.veto_success_rate,
            "action_entropy": self.action_entropy,
        }


def confidence_from_margin(margin: float, temperature: float = 0.10) -> float:
    if temperature <= 0:
        temperature = 0.10
    return sigmoid(margin / temperature)


def compute_agency_metrics(
    *,
    legacy_agency: float,
    contestants: Sequence[Any],
    winner_key: str,
    limbic_winner_key: str,
    inhibited: bool,
    conflict: float,
    pfc_veto: bool,
    temperature: float = 0.10,
) -> AgencyMetrics:
    nets = sorted((float(getattr(c, "net", 0.0)) for c in contestants), reverse=True)
    margin = nets[0] - nets[1] if len(nets) >= 2 else abs(nets[0]) if nets else 0.0
    winner = next((c for c in contestants if getattr(c, "key", "") == winner_key), None)
    limbic = next((c for c in contestants if getattr(c, "key", "") == limbic_winner_key), None)
    pfc_sum = sum(float(getattr(c, "pfc", 0.0)) for c in contestants)
    limbic_sum = sum(float(getattr(c, "limbic", 0.0)) for c in contestants) + 1e-9
    top_down = float(getattr(winner, "pfc", 0.0)) / (float(getattr(winner, "pfc", 0.0)) + float(getattr(winner, "limbic", 0.0)) + 0.15) if winner else 0.0
    # entropía sobre nets normalizados
    import numpy as np

    raw = np.array([max(getattr(c, "net", 0.0), 0.0) for c in contestants], dtype=np.float64)
    s = raw.sum()
    if s > 0:
        p = raw / s
        entropy = float(-np.sum(p * np.log(p + 1e-12)))
    else:
        entropy = 0.0
    return AgencyMetrics(
        legacy_agency_score=float(legacy_agency),
        decision_margin=float(margin),
        confidence_from_margin=confidence_from_margin(margin, temperature),
        top_down_contribution=float(top_down),
        impulse_override_rate=1.0 if inhibited else 0.0,
        pfc_limbic_conflict=float(conflict),
        veto_success_rate=1.0 if pfc_veto else 0.0,
        action_entropy=entropy,
    )
