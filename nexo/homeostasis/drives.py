"""Drives emergentes por desviación del set point."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from nexo.body.body_state import VirtualBody
from nexo.homeostasis.variables import HomeostaticVariable

if TYPE_CHECKING:
    from nexo.core.action_schema import ActionSchema

_LEGACY_ACTION_KEYS = frozenset(
    {
        "eat",
        "rest",
        "flee",
        "approach_caregiver",
        "explore",
        "inspect_distractor",
    }
)


@dataclass
class DriveField:
    """Campo de drives competitivos — no reglas fijas if hunger > 0.8."""

    drives: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_body(cls, body: VirtualBody, *, expected_danger: float = 0.0) -> DriveField:
        variables = {
            "energy": HomeostaticVariable(
                "energy", body.energy, body.energy_setpoint, 0.35, 0.9, 0.15, 1.0, 1.2
            ),
            "hydration": HomeostaticVariable(
                "hydration", body.hydration, body.hydration_setpoint, 0.4, 0.95, 0.2, 1.0, 0.8
            ),
            "fatigue": HomeostaticVariable(
                "fatigue", body.fatigue, 0.2, 0.0, 0.55, 0.0, 0.85, 0.9
            ),
            "social": HomeostaticVariable(
                "social_need", body.social_need, 0.25, 0.1, 0.7, 0.0, 0.95, 0.7
            ),
            "safety": HomeostaticVariable(
                "safety_need", body.safety_need, 0.2, 0.05, 0.6, 0.0, 0.9, 1.0
            ),
        }
        drives: dict[str, float] = {}
        drives["hunger"] = max(0.0, variables["energy"].deviation * variables["energy"].urgency)
        drives["thirst"] = max(0.0, variables["hydration"].deviation * variables["hydration"].urgency)
        drives["rest"] = max(
            0.0,
            (body.fatigue - 0.2) * variables["fatigue"].urgency
            + max(0.0, (0.4 - body.energy)) * 1.5,
        )
        drives["sleep"] = max(0.0, body.sleep_pressure * 0.8)
        drives["social"] = max(0.0, (body.social_need - 0.25) * variables["social"].urgency)
        drives["safety"] = max(
            0.0,
            (body.safety_need - 0.2 + expected_danger * 0.5) * variables["safety"].urgency,
        )
        drives["curiosity"] = max(0.0, 0.25 - body.stress_load * 0.2 - body.fatigue * 0.15)
        return cls(drives=drives)

    def action_bias(self, action: str) -> float:
        """Sesgo competitivo hacia acciones — emerge de drives, no de flags."""
        table = {
            "eat": self.drives.get("hunger", 0.0) * 1.1,
            "rest": (self.drives.get("rest", 0.0) + self.drives.get("sleep", 0.0)) * 0.9,
            "flee": self.drives.get("safety", 0.0) * 1.2,
            "approach_caregiver": self.drives.get("social", 0.0) * 1.0,
            "explore": self.drives.get("curiosity", 0.0) * 0.8,
            "inspect_distractor": self.drives.get("curiosity", 0.0) * 0.6,
        }
        return float(table.get(action, 0.0))

    def schema_bias(self, schema: ActionSchema) -> float:
        """Sesgo desde ActionSchema; equivalente a ``action_bias`` para verbos legacy."""
        if schema.id in _LEGACY_ACTION_KEYS:
            return self.action_bias(schema.id)
        from nexo.core.legacy_action_adapter import drive_for_affordance

        drive = (schema.expected_effect or drive_for_affordance(schema.affordance) or "").strip()
        if drive == "hunger":
            return float(self.drives.get("hunger", 0.0) * 1.1)
        if drive == "rest":
            return float((self.drives.get("rest", 0.0) + self.drives.get("sleep", 0.0)) * 0.9)
        if drive == "safety":
            return float(self.drives.get("safety", 0.0) * 1.2)
        if drive == "social":
            return float(self.drives.get("social", 0.0) * 1.0)
        if drive == "curiosity":
            # Prefer inspectable multiplier when affordance is inspectable.
            mult = 0.6 if schema.affordance == "inspectable" else 0.8
            return float(self.drives.get("curiosity", 0.0) * mult)
        return 0.0

    def dominant(self, n: int = 2) -> tuple[str, ...]:
        ranked = sorted(self.drives.items(), key=lambda x: -x[1])
        return tuple(k for k, v in ranked[:n] if v > 0.05)
