"""Sincronización estado World2D → esquema game3d.js (Sprint 56)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nexo.demo.world2d_headless import World2DHeadlessWorld


REQUIRED_GAME3D_KEYS: frozenset[str] = frozenset({
    "width", "height", "agent", "room", "furniture", "objects", "trees", "tv", "web",
})


def extract_game3d_state(world: Any) -> dict[str, Any]:
    """Extrae dict compatible con `game3d.js` desde facade integrado."""
    w2 = getattr(world, "_world2d", None)
    if w2 is not None and hasattr(w2, "to_dict"):
        return w2.to_dict()
    return {
        "width": 640,
        "height": 480,
        "agent": {"x": float(getattr(world, "agent_x", 0)), "y": 230.0, "dir": 1},
        "room": world.current_room() if hasattr(world, "current_room") else "living",
        "furniture": [],
        "objects": [],
        "trees": [],
        "tv": {},
        "web": {},
    }


def game3d_fidelity_score(state: dict[str, Any]) -> float:
    present = sum(1 for k in REQUIRED_GAME3D_KEYS if k in state)
    key_score = present / max(len(REQUIRED_GAME3D_KEYS), 1)
    furniture_score = min(1.0, len(state.get("furniture") or []) / 8.0)
    agent = state.get("agent") or {}
    agent_score = 1.0 if "x" in agent and "y" in agent else 0.0
    return round(0.4 * key_score + 0.35 * furniture_score + 0.25 * agent_score, 4)


def bind_legacy_world(runtime: Any, brain: Any | None) -> None:
    """Comparte `brain.world` con la facade integrada (Flask unificado)."""
    if brain is None:
        return
    world = runtime.world
    legacy_world = getattr(brain, "world", None)
    if legacy_world is None:
        return
    if hasattr(world, "attach_brain"):
        world.attach_brain(brain)
    elif hasattr(world, "_world2d"):
        try:
            world._world2d = legacy_world
        except AttributeError:
            if hasattr(world, "attach_brain"):
                world.attach_brain(brain)
    companion = runtime.scheduler.config.get("companion_state")
    legacy_comp = getattr(brain, "companion", None)
    if companion is not None and legacy_comp is not None:
        companion.x = float(getattr(legacy_comp, "x", companion.x))
        companion.y = float(getattr(legacy_comp, "y", companion.y))
        companion.agent_dir = int(getattr(legacy_comp, "agent_dir", companion.agent_dir))
        companion.bond = float(getattr(legacy_comp, "bond_with_nexo", companion.bond))


def compare_with_legacy(integrated_state: dict[str, Any], legacy_state: dict[str, Any]) -> dict[str, Any]:
    """Compara tolerancias entre estado integrado y legacy `_world_dict`."""
    int_fc = len(integrated_state.get("furniture") or [])
    leg_fc = len(legacy_state.get("furniture") or [])
    int_room = integrated_state.get("room", "")
    leg_room = legacy_state.get("room", "")
    return {
        "furniture_delta": abs(int_fc - leg_fc),
        "room_match": int_room == leg_room,
        "furniture_tolerance_ok": abs(int_fc - leg_fc) <= 2,
        "sync_score": round(
            0.5 * (1.0 if int_room == leg_room else 0.0)
            + 0.5 * max(0.0, 1.0 - abs(int_fc - leg_fc) / 8.0),
            4,
        ),
    }


@dataclass
class World3DSyncWorld(World2DHeadlessWorld):
    """World2D headless con export game3d sincronizado."""

    sync3d_enabled: bool = True
    sync3d_exports: int = 0

    def game3d_state(self) -> dict[str, Any]:
        state = extract_game3d_state(self)
        if self.sync3d_enabled:
            self.sync3d_exports += 1
        return state

    def game3d_fidelity(self) -> float:
        return game3d_fidelity_score(self.game3d_state())
