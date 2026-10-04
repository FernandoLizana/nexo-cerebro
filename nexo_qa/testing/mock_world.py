"""Deterministic MockWorld for P1 — generic panel/switch, not a browser or RoomWorld."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nexo.core.action_schema import ActionSchema


STATES = ("closed", "armed", "open", "done")


@dataclass
class MockWorld:
    """Tiny state machine: inspect → activate → collect.

    Actions available depend on `phase`. No RoomWorld verbs, no RNG.
    """

    seed: int = 42
    phase: str = "closed"
    ticks: int = 0
    action_history: list[str] = field(default_factory=list)
    episodes: list[str] = field(default_factory=list)
    last_error: str | None = None

    def percepts_for_agent(self) -> list[tuple[str, float, tuple[float, ...]]]:
        if self.phase == "closed":
            return [("panel", 0.6, (0.0, 0.0, 1.0)), ("switch", 0.4, (0.2, 0.1, 0.0))]
        if self.phase == "armed":
            return [("panel", 0.5, (0.0, 1.0, 1.0)), ("switch", 0.8, (1.0, 0.2, 0.0))]
        if self.phase == "open":
            return [("target", 0.9, (1.0, 1.0, 0.2))]
        return [("complete", 0.3, (0.1, 0.1, 0.1))]

    def available_actions(self) -> tuple[str, ...]:
        if self.phase == "closed":
            return ("inspect_panel", "wait")
        if self.phase == "armed":
            return ("activate_switch", "step_back")
        if self.phase == "open":
            return ("collect_target", "step_back")
        return ("finish",)

    def action_info(self, action: str) -> dict[str, Any]:
        table = {
            "inspect_panel": {"base_value": 0.55, "cost_energy": 0.02, "risk": 0.0, "modality": "panel"},
            "wait": {"base_value": 0.08, "cost_energy": 0.0, "risk": 0.0, "modality": "panel"},
            "activate_switch": {"base_value": 0.6, "cost_energy": 0.04, "risk": 0.05, "modality": "switch"},
            "collect_target": {"base_value": 0.75, "cost_energy": 0.03, "risk": 0.0, "modality": "target"},
            "step_back": {"base_value": 0.12, "cost_energy": 0.02, "risk": 0.0, "modality": "panel"},
            "finish": {"base_value": 0.2, "cost_energy": 0.0, "risk": 0.0, "modality": "complete"},
        }
        return table.get(action, {"base_value": 0.0, "cost_energy": 0.05, "risk": 0.1, "modality": ""})

    def action_schemas(self) -> tuple[ActionSchema, ...]:
        specs = {
            "inspect_panel": ("inspect", "panel", "inspectable", "reveal"),
            "wait": ("wait", "panel", "navigable", "idle"),
            "activate_switch": ("activate", "switch", "selectable", "open_panel"),
            "collect_target": ("collect", "target", "consumable", "obtain"),
            "step_back": ("navigate", "panel", "navigable", "return"),
            "finish": ("complete", "complete", "selectable", "end"),
        }
        schemas = []
        for action_id in self.available_actions():
            info = self.action_info(action_id)
            action_type, target, affordance, effect = specs[action_id]
            schemas.append(
                ActionSchema(
                    id=action_id,
                    label=action_id.replace("_", " "),
                    action_type=action_type,
                    target=target,
                    affordance=affordance,
                    expected_effect=effect,
                    estimated_cost=float(info["cost_energy"]),
                    risk=float(info["risk"]),
                    metadata={"source": "mock_world", "phase": self.phase},
                )
            )
        return tuple(schemas)

    def apply_action(self, action: str) -> dict[str, Any]:
        self.ticks += 1
        if action not in self.available_actions():
            self.last_error = "action_unavailable"
            return {
                "reward": 0.0,
                "homeostatic_deltas": {},
                "encoded_memory": None,
                "accepted": False,
                "success": False,
                "error": "action_unavailable",
            }
        self.action_history.append(action)
        self.last_error = None
        reward = 0.08
        previous = self.phase
        if self.phase == "closed" and action == "inspect_panel":
            self.phase = "armed"
            reward = 0.2
        elif self.phase == "closed" and action == "wait":
            reward = 0.01
        elif self.phase == "armed" and action == "activate_switch":
            self.phase = "open"
            reward = 0.45
        elif self.phase == "open" and action == "collect_target":
            self.phase = "done"
            reward = 0.8
        elif action == "step_back":
            self.phase = "closed"
            reward = 0.02
        elif self.phase == "done" and action == "finish":
            reward = 0.1
        return {
            "reward": reward,
            "homeostatic_deltas": {"energy": -0.01},
            "encoded_memory": None,
            "accepted": True,
            "success": True,
            "error": None,
            "from_phase": previous,
            "to_phase": self.phase,
        }

    def sync_from_body(self, body: object) -> None:
        return None
