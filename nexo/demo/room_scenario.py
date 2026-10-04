"""Escenario mínimo: habitación con recursos, distractor, peligro y cuidador."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class RoomWorld:
    """Mundo simulado simple para demo recurrente integrada."""

    energy: float = 0.55
    hydration: float = 0.7
    food_available: bool = True
    distractor_salience: float = 0.45
    danger_level: float = 0.15
    caregiver_present: bool = True
    caregiver_trust: float = 0.6
    ticks: int = 0
    action_history: list[str] = field(default_factory=list)
    episodes: list[str] = field(default_factory=list)
    rng_noise: float = 0.05

    def percepts_for_agent(self) -> list[tuple[str, float, tuple[float, ...]]]:
        percepts: list[tuple[str, float, tuple[float, ...]]] = []
        if self.food_available:
            percepts.append(("food", 0.35 + (1.0 - self.energy) * 0.4, (1.0, 0.2, self.energy)))
        percepts.append(("distractor", self.distractor_salience, (0.8, 0.9, 0.1)))
        if self.danger_level > 0.1:
            percepts.append(("danger", self.danger_level, (0.1, 0.1, 0.9)))
        if self.caregiver_present:
            percepts.append(("caregiver", 0.25 + self.caregiver_trust * 0.2, (0.5, 0.8, 0.5)))
        return percepts

    def sync_from_body(self, body: object) -> None:
        """Sincroniza variables visibles del mundo con el cuerpo virtual."""
        self.energy = float(getattr(body, "energy", self.energy))

    def available_actions(self) -> tuple[str, ...]:
        actions = ["explore", "rest"]
        if self.food_available:
            actions.append("eat")
        if self.danger_level > 0.2:
            actions.append("flee")
        if self.caregiver_present:
            actions.append("approach_caregiver")
        actions.append("inspect_distractor")
        return tuple(actions)

    def action_info(self, action: str) -> dict:
        table = {
            "eat": {"base_value": 0.3, "cost_energy": 0.05, "risk": 0.0, "modality": "food"},
            "explore": {"base_value": 0.15, "cost_energy": 0.08, "risk": 0.05, "modality": "distractor"},
            "rest": {"base_value": 0.1, "cost_energy": -0.02, "risk": 0.0, "modality": "interoception"},
            "flee": {"base_value": 0.2, "cost_energy": 0.12, "risk": 0.0, "modality": "danger"},
            "approach_caregiver": {
                "base_value": 0.25,
                "cost_energy": 0.06,
                "risk": 0.02,
                "modality": "caregiver",
            },
            "inspect_distractor": {
                "base_value": 0.22,
                "cost_energy": 0.04,
                "risk": 0.08,
                "modality": "distractor",
            },
        }
        return table.get(action, {"base_value": 0.0, "cost_energy": 0.05, "risk": 0.1, "modality": ""})

    def apply_action(self, action: str) -> dict:
        self.ticks += 1
        self.action_history.append(action)
        info = self.action_info(action)
        reward = 0.0
        homeo: dict[str, float] = {"energy": -info.get("cost_energy", 0.03)}
        memory_id = None

        if action == "eat" and self.food_available:
            reward = 0.6
            homeo["energy"] = 0.0  # aplicado vía MetabolismEngine en motor process
            self.food_available = False
            memory_id = uuid4().hex[:8]
        elif action == "rest":
            reward = 0.15
            homeo["energy"] = 0.0
            homeo["fatigue"] = 0.0
        elif action == "flee":
            reward = 0.25 if self.danger_level > 0.2 else -0.05
            self.danger_level = max(0.0, self.danger_level - 0.25)
        elif action == "approach_caregiver" and self.caregiver_present:
            reward = 0.35
            self.caregiver_trust = min(1.0, self.caregiver_trust + 0.05)
            memory_id = uuid4().hex[:8]
        elif action == "inspect_distractor":
            reward = 0.1
            self.distractor_salience = max(0.1, self.distractor_salience - 0.08)
        elif action == "explore":
            reward = 0.08
            if self.ticks % 7 == 0:
                self.danger_level = min(0.6, self.danger_level + 0.12)

        self.energy = max(0.0, min(1.0, self.energy + homeo.get("energy", 0.0)))
        if memory_id:
            self.episodes.append(memory_id)

        return {
            "reward": reward,
            "homeostatic_deltas": homeo,
            "encoded_memory": memory_id,
        }
