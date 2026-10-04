"""Teoría de la mente simplificada — inferencia sobre el cuidador."""

from __future__ import annotations

from dataclasses import dataclass, field

from nexo.social.agent_model import SocialAgent


@dataclass
class TheoryOfMindInference:
    other_belief: str
    predicted_response: str
    confidence: float
    social_action_bias: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, str | float | dict[str, float]]:
        return {
            "other_belief": self.other_belief,
            "predicted_response": self.predicted_response,
            "confidence": round(self.confidence, 4),
            "social_action_bias": {k: round(v, 4) for k, v in self.social_action_bias.items()},
        }


@dataclass
class TheoryOfMindEngine:
    """Inferencia funcional sobre estados mentales del otro."""

    last: TheoryOfMindInference | None = field(default=None, init=False)

    def infer(
        self,
        *,
        caregiver: SocialAgent,
        social_need: float,
        recent_action: str | None,
        energy: float,
    ) -> TheoryOfMindInference:
        if caregiver.presence < 0.5:
            inference = TheoryOfMindInference(
                other_belief="caregiver_absent",
                predicted_response="silence",
                confidence=0.7,
            )
        elif social_need > 0.5 and caregiver.trust > 0.5:
            inference = TheoryOfMindInference(
                other_belief="caregiver_wants_contact",
                predicted_response="comfort_offer",
                confidence=min(0.95, 0.4 + caregiver.trust * 0.5),
                social_action_bias={"approach_caregiver": 0.15 + social_need * 0.2},
            )
        elif energy < 0.35 and caregiver.help_availability > 0.5:
            inference = TheoryOfMindInference(
                other_belief="caregiver_can_help_regulate",
                predicted_response="encourage_rest_or_food",
                confidence=0.55 + caregiver.trust * 0.25,
                social_action_bias={"approach_caregiver": 0.1, "eat": 0.08, "rest": 0.06},
            )
        elif recent_action == "approach_caregiver":
            inference = TheoryOfMindInference(
                other_belief="caregiver_received_approach",
                predicted_response="acknowledge",
                confidence=0.65,
                social_action_bias={},
            )
        else:
            inference = TheoryOfMindInference(
                other_belief="caregiver_available",
                predicted_response="monitor",
                confidence=0.35 + caregiver.trust * 0.3,
                social_action_bias={"approach_caregiver": social_need * 0.12},
            )

        self.last = inference
        return inference
