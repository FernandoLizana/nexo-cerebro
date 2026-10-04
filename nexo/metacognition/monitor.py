"""Monitor metacognitivo — claridad, duda y estado fenomenológico funcional."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MetacognitiveState:
    clarity: float = 0.3
    doubt: float = 0.2
    confidence: float = 0.5
    felt: str = "difuso"
    agency: float = 0.0

    def to_dict(self) -> dict[str, float | str]:
        return {
            "clarity": round(self.clarity, 4),
            "doubt": round(self.doubt, 4),
            "confidence": round(self.confidence, 4),
            "felt": self.felt,
            "agency": round(self.agency, 4),
        }


@dataclass
class MetacognitiveMonitor:
    """Evalúa calidad del procesamiento consciente sin verbalizar."""

    last: MetacognitiveState = field(default_factory=MetacognitiveState)

    def evaluate(
        self,
        *,
        winner_salience: float,
        total_salience: float,
        conflict: float,
        surprise: float,
        sleep_pressure: float,
        deliberation_confidence: float = 0.5,
        pfc_veto: bool = False,
    ) -> MetacognitiveState:
        total = max(total_salience, 0.01)
        clarity = max(0.08, min(1.0, winner_salience / total * 1.3))
        doubt = max(0.0, min(1.0, conflict + surprise * 0.25 + (0.15 if pfc_veto else 0.0)))
        confidence = max(0.0, min(1.0, winner_salience - doubt * 0.35 + deliberation_confidence * 0.2))

        if sleep_pressure > 0.65:
            clarity *= 0.55
            felt = "somnoliento"
        elif doubt > 0.5 and clarity > 0.3:
            felt = "dividido"
        elif clarity > 0.55:
            felt = "claro"
        elif clarity > 0.3:
            felt = "difuso"
        else:
            felt = "nublado"

        agency = max(0.0, min(1.0, deliberation_confidence * (1.0 - doubt * 0.4)))
        state = MetacognitiveState(
            clarity=clarity,
            doubt=doubt,
            confidence=confidence,
            felt=felt,
            agency=agency,
        )
        self.last = state
        return state
