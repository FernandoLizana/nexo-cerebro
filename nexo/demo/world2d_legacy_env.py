"""Mundo 2D legacy enriquecido — expone semántica hogar World2D (Sprint 40)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import numpy as np


@dataclass
class World2DLegacyEnvWorld:
    """Facade integrado sobre `brain.world.World2D` con mobiliario y habitaciones."""

    seed: int = 42
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
    rooms_visited: set[str] = field(default_factory=set)
    object_interactions: int = 0
    legacy_env_enabled: bool = True
    legacy_actions_enabled: bool = False
    full_actions_enabled: bool = False
    _world2d: Any = field(default=None, repr=False)
    _start_x: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        from brain.world import World2D

        self._world2d = World2D()
        self._world2d.bind_rng(np.random.default_rng(self.seed))
        self._world2d.ensure_home()
        self._start_x = float(self._world2d.agent_x)
        self.rooms_visited.add(self.current_room())

    @property
    def agent_x(self) -> float:
        return float(self._world2d.agent_x)

    @property
    def distance_traveled(self) -> float:
        return abs(float(self._world2d.agent_x) - self._start_x)

    @property
    def furniture_count(self) -> int:
        return len(self._world2d.furniture)

    @property
    def object_count(self) -> int:
        return len(self._world2d.objects)

    def current_room(self) -> str:
        try:
            return str(self._world2d.current_room())
        except Exception:
            return "casa"

    def env_fidelity_score(self) -> float:
        """Heurística 0–1: mobiliario + habitaciones + interacciones."""
        room_score = min(1.0, len(self.rooms_visited) / 4.0)
        furniture_score = min(1.0, self.furniture_count / 12.0)
        interact_score = min(1.0, self.object_interactions / max(self.ticks, 1))
        return round(0.4 * furniture_score + 0.35 * room_score + 0.25 * interact_score, 4)

    def sync_from_body(self, body: object) -> None:
        self.energy = float(getattr(body, "energy", self.energy))

    def percepts_for_agent(self) -> list[tuple[str, float, tuple[float, ...]]]:
        percepts: list[tuple[str, float, tuple[float, ...]]] = []
        room = self.current_room()
        nx = self.agent_x / max(self._world2d.width, 1.0)
        percepts.append(("spatial", 0.35, (nx, 0.5, self.energy)))
        percepts.append(("room", 0.25, (hash(room) % 100 / 100.0, self.furniture_count, self.object_count)))
        if self.food_available:
            percepts.append(("food", 0.3 + (1.0 - self.energy) * 0.35, (1.0, 0.2, self.energy)))
        percepts.append(("distractor", self.distractor_salience, (0.8, 0.9, 0.1)))
        if self.caregiver_present:
            percepts.append(("caregiver", 0.2 + self.caregiver_trust * 0.2, (0.5, 0.8, 0.5)))
        if self.danger_level > 0.25:
            percepts.append(("danger", self.danger_level, (1.0, 0.1, 0.1)))
        return percepts

    def available_actions(self) -> tuple[str, ...]:
        actions = ["explore", "rest", "inspect_distractor"]
        if self.food_available:
            actions.append("eat")
        if self.caregiver_present:
            actions.append("approach_caregiver")
        if self.full_actions_enabled or self.legacy_env_enabled:
            actions.append("flee")
        return tuple(actions)

    def action_info(self, action: str) -> dict:
        table = {
            "eat": {"base_value": 0.3, "cost_energy": 0.05, "risk": 0.0, "modality": "food"},
            "explore": {"base_value": 0.18, "cost_energy": 0.07, "risk": 0.04, "modality": "spatial"},
            "rest": {"base_value": 0.1, "cost_energy": -0.02, "risk": 0.0, "modality": "interoception"},
            "approach_caregiver": {"base_value": 0.22, "cost_energy": 0.06, "risk": 0.02, "modality": "caregiver"},
            "inspect_distractor": {"base_value": 0.2, "cost_energy": 0.04, "risk": 0.06, "modality": "distractor"},
            "flee": {"base_value": 0.05, "cost_energy": 0.1, "risk": 0.12, "modality": "spatial"},
        }
        return table.get(action, {"base_value": 0.0, "cost_energy": 0.05, "risk": 0.1, "modality": ""})

    def apply_action(self, action: str) -> dict:
        if self.legacy_actions_enabled or self.full_actions_enabled:
            from nexo.demo.world2d_actions import map_legacy_action

            action = map_legacy_action(action, full=self.full_actions_enabled)
        self.ticks += 1
        self.action_history.append(action)
        info = self.action_info(action)
        reward = 0.0
        homeo: dict[str, float] = {"energy": -info.get("cost_energy", 0.03)}
        memory_id = None

        if action == "explore":
            self._world2d.agent_x = float(
                np.clip(self._world2d.agent_x + 14.0 * self._world2d.agent_dir, 0, self._world2d.width)
            )
            if self.ticks % 7 == 0:
                self._world2d.agent_dir *= -1
            self.rooms_visited.add(self.current_room())
            reward = 0.12
            self.object_interactions += 1
        elif action == "eat" and self.food_available:
            reward = 0.55
            self.food_available = False
            memory_id = uuid4().hex[:8]
            self.object_interactions += 1
        elif action == "rest":
            reward = 0.12
        elif action == "approach_caregiver" and self.caregiver_present:
            reward = 0.3
            self.caregiver_trust = min(1.0, self.caregiver_trust + 0.04)
        elif action == "inspect_distractor":
            reward = 0.08
            self.distractor_salience = max(0.1, self.distractor_salience - 0.06)
            self.object_interactions += 1
        elif action == "flee":
            self._world2d.agent_x = float(
                np.clip(self._world2d.agent_x - 20.0 * self._world2d.agent_dir, 0, self._world2d.width)
            )
            self.danger_level = max(0.0, self.danger_level - 0.1)
            reward = 0.06

        if self.legacy_env_enabled and self.furniture_count > 0 and self.ticks % 11 == 0:
            self.object_interactions += 1

        self.energy = max(0.0, min(1.0, self.energy + homeo.get("energy", 0.0)))
        if memory_id:
            self.episodes.append(memory_id)
        return {"reward": reward, "homeostatic_deltas": homeo, "encoded_memory": memory_id}
