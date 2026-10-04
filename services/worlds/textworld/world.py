"""TextWorld — cheap, seeded, multi-Being text arena (S5)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from nexo.core.action_schema import ActionSchema

from services.worlds.adapter import WorldSpec
from services.worlds.textworld.events import make_interaction_event, make_world_event


DEFAULT_PLACES: tuple[str, ...] = ("meadow", "stream", "den", "nest", "clearing")


@dataclass
class TextWorld:
    """Reproducible text places where Beings can co-locate and interact."""

    seed: int = 0
    places: tuple[str, ...] = DEFAULT_PLACES
    clock: int = 0
    locations: dict[str, str] = field(default_factory=dict)
    personalities: dict[str, dict[str, float]] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(int(self.seed))
        if not self.places:
            raise ValueError("TextWorld requires at least one place")

    @property
    def spec(self) -> WorldSpec:
        return WorldSpec(world_type="TextWorld", seed=self.seed, version="textworld-v1")

    def reset(self, seed: int | None = None) -> None:
        if seed is not None:
            self.seed = int(seed)
        self._rng = random.Random(self.seed)
        self.clock = 0
        self.locations.clear()
        self.events.clear()

    def place_being(self, being_id: str, place: str | None = None) -> str:
        if place is None:
            place = self.places[self._rng.randrange(0, len(self.places))]
        if place not in self.places:
            raise ValueError(f"unknown place: {place}")
        self.locations[being_id] = place
        self.personalities.setdefault(being_id, {})
        self.events.append(
            make_world_event(
                event_type="BEING_PLACED",
                tick=self.clock,
                payload={"being_id": being_id, "place": place},
            )
        )
        return place

    def set_personality(self, being_id: str, traits: dict[str, float]) -> None:
        self.personalities[being_id] = dict(traits)

    def location_of(self, being_id: str) -> str:
        if being_id not in self.locations:
            raise KeyError(being_id)
        return self.locations[being_id]

    def beings_at(self, place: str) -> list[str]:
        return sorted(bid for bid, loc in self.locations.items() if loc == place)

    def agent_view(self, being_id: str) -> AgentView:
        if being_id not in self.locations:
            raise KeyError(being_id)
        return AgentView(world=self, being_id=being_id)

    def percepts_for(self, being_id: str) -> list[tuple[str, float, tuple[float, ...]]]:
        place = self.location_of(being_id)
        others = [b for b in self.beings_at(place) if b != being_id]
        percepts: list[tuple[str, float, tuple[float, ...]]] = [
            (f"place:{place}", 0.8, (1.0, 0.0, 0.0)),
        ]
        for other in others:
            percepts.append((f"being:{other}", 0.6, (0.0, 1.0, 0.0)))
        return percepts

    def available_actions_for(self, being_id: str) -> tuple[str, ...]:
        place = self.location_of(being_id)
        actions: list[str] = ["observe", "rest", "forage"]
        for dest in self.places:
            if dest != place:
                actions.append(f"move_{dest}")
        for other in self.beings_at(place):
            if other == being_id:
                continue
            actions.append(f"greet_{other}")
            actions.append(f"play_{other}")
        return tuple(sorted(actions))

    def action_info_for(self, being_id: str, action: str) -> dict[str, Any]:
        _ = being_id
        if action.startswith("move_"):
            return {
                "base_value": 0.3,
                "cost_energy": 0.05,
                "risk": 0.05,
                "modality": "spatial",
                "action_type": "move",
                "affordance": "navigable",
                "expected_effect": "exploration",
            }
        if action.startswith("greet_") or action.startswith("play_"):
            return {
                "base_value": 0.4,
                "cost_energy": 0.02,
                "risk": 0.02,
                "modality": "social",
                "action_type": "social",
                "affordance": "approachable",
                "expected_effect": "social",
            }
        table = {
            "observe": ("inspect", "inspectable", "curiosity", 0.01),
            "rest": ("recover", "restorable", "rest", 0.0),
            "forage": ("explore", "consumable", "hunger", 0.04),
        }
        action_type, affordance, effect, cost = table.get(action, ("act", "navigable", "curiosity", 0.01))
        return {
            "base_value": 0.25,
            "cost_energy": cost,
            "risk": 0.0,
            "modality": "text",
            "action_type": action_type,
            "affordance": affordance,
            "expected_effect": effect,
        }

    def apply_action_for(self, being_id: str, action: str) -> dict[str, Any]:
        available = self.available_actions_for(being_id)
        if action not in available:
            return {"accepted": False, "error": "action_unavailable", "reward": 0.0}
        place = self.location_of(being_id)
        reward = 0.05
        outcome = "ok"
        response = None
        other: str | None = None
        interaction_kind = "OBSERVE"

        if action.startswith("move_"):
            dest = action.removeprefix("move_")
            self.locations[being_id] = dest
            place = dest
            interaction_kind = "MOVE"
            reward = 0.02
        elif action == "rest":
            interaction_kind = "REST"
            reward = 0.03
        elif action == "forage":
            interaction_kind = "FORAGE"
            reward = 0.08 if self._rng.random() < 0.55 else 0.01
        elif action == "observe":
            interaction_kind = "OBSERVE"
            reward = 0.04
        elif action.startswith("greet_"):
            other = action.removeprefix("greet_")
            interaction_kind = "GREET"
            response = "ack"
            reward = 0.1
            outcome = "social_contact"
        elif action.startswith("play_"):
            other = action.removeprefix("play_")
            interaction_kind = "PLAY"
            response = "play_accepted"
            reward = 0.12
            outcome = "play"

        ie = make_interaction_event(
            interaction_id=f"ix-{self.clock}-{being_id}-{action}",
            tick=self.clock,
            being_a=being_id,
            being_b=other,
            action=interaction_kind,
            response=response,
            outcome=outcome,
            place=place,
            context={"raw_action": action},
        )
        self.events.append(ie)

        return {
            "accepted": True,
            "reward": reward,
            "homeostatic_deltas": {},
            "encoded_memory": None,
            "place": place,
            "action": action,
        }

    def choose_action(self, being_id: str) -> str:
        """Deterministic utility-ish policy using personality + RNG."""
        actions = self.available_actions_for(being_id)
        traits = self.personalities.get(being_id) or {}
        scored: list[tuple[float, str]] = []
        for action in actions:
            score = 0.1
            if action.startswith("move_"):
                score += 0.4 * float(traits.get("exploration", 0.5))
            elif action.startswith("greet_") or action.startswith("play_"):
                score += 0.55 * float(traits.get("sociability", 0.5))
                score += 0.2 * float(traits.get("trust", 0.5))
            elif action == "observe":
                score += 0.45 * float(traits.get("curiosity", 0.5))
            elif action == "forage":
                score += 0.35 * float(traits.get("persistence", 0.5))
            elif action == "rest":
                score += 0.3 * float(traits.get("patience", 0.5))
            score += self._rng.random() * 0.05
            scored.append((-score, action))
        scored.sort()
        return scored[0][1]

    def tick(self) -> list[dict[str, Any]]:
        """Advance world: each being acts once in sorted id order."""
        self.clock += 1
        before = len(self.events)
        for being_id in sorted(self.locations):
            action = self.choose_action(being_id)
            self.apply_action_for(being_id, action)
        emitted = self.events[before:]
        self.events.append(
            make_world_event(
                event_type="WORLD_TICK",
                tick=self.clock,
                payload={
                    "beings": sorted(self.locations),
                    "locations": dict(sorted(self.locations.items())),
                },
            )
        )
        return emitted + self.events[-1:]

    def snapshot(self) -> dict[str, Any]:
        return {
            "spec": {
                "world_type": self.spec.world_type,
                "seed": self.spec.seed,
                "version": self.spec.version,
            },
            "tick": self.clock,
            "places": list(self.places),
            "locations": dict(sorted(self.locations.items())),
            "event_count": len(self.events),
        }


@dataclass
class AgentView:
    """EnvironmentProtocol-compatible view for one Being in TextWorld."""

    world: TextWorld
    being_id: str

    def percepts_for_agent(self) -> list[tuple[str, float, tuple[float, ...]]]:
        return self.world.percepts_for(self.being_id)

    def available_actions(self) -> tuple[str, ...]:
        return self.world.available_actions_for(self.being_id)

    def action_info(self, action: str) -> dict[str, Any]:
        return self.world.action_info_for(self.being_id, action)

    def apply_action(self, action: str) -> dict[str, Any]:
        return self.world.apply_action_for(self.being_id, action)

    def action_schemas(self) -> tuple[ActionSchema, ...]:
        schemas: list[ActionSchema] = []
        for action in self.available_actions():
            info = self.action_info(action)
            schemas.append(
                ActionSchema(
                    id=action,
                    label=action.replace("_", " "),
                    action_type=str(info.get("action_type") or "act"),
                    affordance=str(info.get("affordance") or "navigable"),
                    expected_effect=str(info.get("expected_effect") or "curiosity"),
                    estimated_cost=float(info.get("cost_energy") or 0.01),
                    risk=float(info.get("risk") or 0.0),
                    metadata={"world": "textworld", "place": self.world.location_of(self.being_id)},
                )
            )
        return tuple(schemas)
