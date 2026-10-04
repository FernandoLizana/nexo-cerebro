"""Facade demo — alias directo de `brain.world` (Fase 12)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nexo.demo.world2d_legacy_env import World2DLegacyEnvWorld


@dataclass
class WorldDemoFacade:
    """Mundo integrado que reutiliza la instancia World2D del legacy brain."""

    seed: int = 42
    legacy_env_enabled: bool = True
    legacy_actions_enabled: bool = True
    full_actions_enabled: bool = True
    demo_facade_enabled: bool = True
    ticks: int = 0
    action_history: list[str] = field(default_factory=list)
    episodes: list[str] = field(default_factory=list)
    rooms_visited: set[str] = field(default_factory=set)
    _env: World2DLegacyEnvWorld | None = field(default=None, repr=False)
    _brain: Any = field(default=None, repr=False)

    def attach_brain(self, brain: Any) -> None:
        self._brain = brain
        env = World2DLegacyEnvWorld(
            seed=self.seed,
            legacy_env_enabled=self.legacy_env_enabled,
            legacy_actions_enabled=self.legacy_actions_enabled,
            full_actions_enabled=self.full_actions_enabled,
        )
        env._world2d = brain.world
        env._start_x = float(brain.world.agent_x)
        env.rooms_visited = set(self.rooms_visited)
        env.ticks = self.ticks
        env.action_history = list(self.action_history)
        env.episodes = list(self.episodes)
        self._env = env
        self.rooms_visited.add(env.current_room())

    def _require_env(self) -> World2DLegacyEnvWorld:
        if self._env is None:
            raise RuntimeError("WorldDemoFacade.attach_brain() required before use")
        return self._env

    @property
    def _world2d(self) -> Any:
        return self._require_env()._world2d

    @property
    def agent_x(self) -> float:
        return self._require_env().agent_x

    @property
    def furniture_count(self) -> int:
        return self._require_env().furniture_count

    def current_room(self) -> str:
        return self._require_env().current_room()

    def apply_action(self, action: str) -> dict:
        outcome = self._require_env().apply_action(action)
        self.ticks = self._env.ticks
        self.action_history = list(self._env.action_history)
        self.episodes = list(self._env.episodes)
        self.rooms_visited = set(self._env.rooms_visited)
        return outcome

    def sync_from_body(self, body: object) -> None:
        self._require_env().sync_from_body(body)

    def percepts_for_agent(self) -> list[tuple[str, float, tuple[float, ...]]]:
        return self._require_env().percepts_for_agent()

    def action_info(self, action: str) -> dict:
        return self._require_env().action_info(action)

    def game3d_state(self) -> dict[str, Any]:
        from nexo.demo.world3d_sync import extract_game3d_state

        return extract_game3d_state(self)

    def facade_fidelity_score(self) -> float:
        env = self._env
        if env is None:
            return 0.0
        base = env.env_fidelity_score()
        attached = self._brain is not None and env._world2d is getattr(self._brain, "world", None)
        return round(min(1.0, base + (0.25 if attached else 0.0)), 4)
