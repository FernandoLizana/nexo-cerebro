"""Estado corporal persistente del agente."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActionCost:
    energy: float = 0.03
    fatigue: float = 0.01
    hydration: float = 0.005
    risk: float = 0.0
    cognitive_load: float = 0.0
    duration_ticks: int = 1


@dataclass
class VirtualBody:
    """Cuerpo simulado con variables homeostáticas acopladas al scheduler."""

    energy: float = 0.72
    hydration: float = 0.75
    temperature: float = 37.0
    pain: float = 0.0
    fatigue: float = 0.15
    sleep_pressure: float = 0.1
    stress_load: float = 0.1
    social_need: float = 0.35
    safety_need: float = 0.25
    motor_capability: float = 1.0
    sensory_integrity: float = 1.0
    injury: float = 0.0

    # Set points
    energy_setpoint: float = 0.65
    hydration_setpoint: float = 0.7
    temperature_setpoint: float = 37.0

    def clamp(self) -> None:
        self.energy = max(0.0, min(1.0, self.energy))
        self.hydration = max(0.0, min(1.0, self.hydration))
        self.temperature = max(34.0, min(42.0, self.temperature))
        self.pain = max(0.0, min(1.0, self.pain))
        self.fatigue = max(0.0, min(1.0, self.fatigue))
        self.sleep_pressure = max(0.0, min(1.0, self.sleep_pressure))
        self.stress_load = max(0.0, min(1.0, self.stress_load))
        self.social_need = max(0.0, min(1.0, self.social_need))
        self.safety_need = max(0.0, min(1.0, self.safety_need))
        self.motor_capability = max(0.0, min(1.0, self.motor_capability))
        self.sensory_integrity = max(0.0, min(1.0, self.sensory_integrity))

    def apply_cost(self, cost: ActionCost) -> None:
        self.energy -= cost.energy
        self.fatigue += cost.fatigue
        self.hydration -= cost.hydration
        self.clamp()

    def to_homeostatic_dict(self) -> dict[str, float]:
        return {
            "energy": self.energy,
            "hydration": self.hydration,
            "temperature": self.temperature,
            "pain": self.pain,
            "fatigue": self.fatigue,
            "sleep_pressure": self.sleep_pressure,
            "stress_load": self.stress_load,
            "social_need": self.social_need,
            "safety_need": self.safety_need,
        }

    @classmethod
    def action_costs(cls) -> dict[str, ActionCost]:
        return {
            "eat": ActionCost(energy=0.04, fatigue=0.005, hydration=-0.02, risk=0.0),
            "explore": ActionCost(energy=0.07, fatigue=0.015, risk=0.05, cognitive_load=0.02),
            "rest": ActionCost(energy=-0.015, fatigue=-0.04, hydration=-0.005),
            "flee": ActionCost(energy=0.11, fatigue=0.025, risk=0.0),
            "approach_caregiver": ActionCost(energy=0.028, fatigue=0.008, risk=0.02),
            "inspect_distractor": ActionCost(energy=0.022, fatigue=0.006, cognitive_load=0.03),
            "think": ActionCost(energy=0.02, fatigue=0.012, cognitive_load=0.08),
        }
