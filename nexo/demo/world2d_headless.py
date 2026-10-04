"""World2D headless — locomoción step_toward + mobiliario (Sprint 52)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import numpy as np

from nexo.demo.world2d_legacy_env import World2DLegacyEnvWorld


@dataclass
class World2DHeadlessWorld(World2DLegacyEnvWorld):
    """World2D con step_toward y proximidad a mobiliario (headless)."""

    headless_enabled: bool = True
    headless_steps: int = 0
    furniture_proximity_events: int = 0

    def headless_fidelity_score(self) -> float:
        base = self.env_fidelity_score()
        step_score = min(1.0, self.headless_steps / max(self.ticks, 1))
        prox_score = min(1.0, self.furniture_proximity_events / max(self.furniture_count, 1))
        return round(0.5 * base + 0.25 * step_score + 0.25 * prox_score, 4)

    def _check_furniture_proximity(self) -> None:
        w = self._world2d
        for fu in w.furniture[:8]:
            cx = fu.x + fu.w / 2
            cy = fu.y + fu.h / 2
            dist = ((cx - w.agent_x) ** 2 + (cy - w.agent_y) ** 2) ** 0.5
            if dist < 55:
                self.furniture_proximity_events += 1
                break

    def apply_action(self, action: str) -> dict:
        if self.headless_enabled and action == "explore":
            w = self._world2d
            target_x = float(np.clip(w.agent_x + 40.0 * w.agent_dir, 40, w.width - 40))
            steps = w.step_toward(target_x, w.agent_y, max_steps=3, speed=14.0)
            self.headless_steps += int(steps)
            self._check_furniture_proximity()
        outcome = super().apply_action(action)
        if self.headless_enabled:
            self.rooms_visited.add(self.current_room())
        return outcome
