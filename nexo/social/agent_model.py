"""Modelo del agente social (cuidador)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SocialAgent:
    name: str = "cuidador"
    trust: float = 0.6
    attachment: float = 0.4
    presence: float = 1.0
    inferred_intent: str = "support"
    help_availability: float = 0.5

    def to_dict(self) -> dict[str, str | float]:
        return {
            "name": self.name,
            "trust": round(self.trust, 4),
            "attachment": round(self.attachment, 4),
            "presence": round(self.presence, 4),
            "inferred_intent": self.inferred_intent,
            "help_availability": round(self.help_availability, 4),
        }


@dataclass
class CaregiverModel:
    """Estado social del cuidador en RoomWorld."""

    agent: SocialAgent = field(default_factory=SocialAgent)
    interaction_count: int = 0

    def sync_from_world(self, world: object) -> SocialAgent:
        present = bool(getattr(world, "caregiver_present", False))
        trust = float(getattr(world, "caregiver_trust", 0.5))
        self.agent.trust = trust
        self.agent.presence = 1.0 if present else 0.0
        self.agent.attachment = min(1.0, 0.25 + trust * 0.65)
        self.agent.help_availability = min(1.0, trust * 0.7 + (0.2 if present else 0.0))
        if trust > 0.7:
            self.agent.inferred_intent = "support"
        elif trust > 0.4:
            self.agent.inferred_intent = "neutral"
        else:
            self.agent.inferred_intent = "distant"
        return self.agent

    def register_interaction(self) -> None:
        self.interaction_count += 1
        self.agent.attachment = min(1.0, self.agent.attachment + 0.04)
