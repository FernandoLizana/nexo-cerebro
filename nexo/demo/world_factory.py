"""Factory de mundos demo integrados."""

from __future__ import annotations

from nexo.demo.extended_room import ExtendedRoomWorld
from nexo.demo.room_scenario import RoomWorld
from nexo.demo.world_demo_facade import WorldDemoFacade
from nexo.demo.world3d_sync import World3DSyncWorld
from nexo.demo.world2d_headless import World2DHeadlessWorld
from nexo.demo.world2d_legacy_env import World2DLegacyEnvWorld
from nexo.demo.world2d_lite import World2DLiteWorld


def create_world(mode: str = "room", *, seed: int = 42) -> RoomWorld:
    if mode == "extended":
        return ExtendedRoomWorld()
    if mode == "world_demo_facade":
        return WorldDemoFacade(seed=seed, legacy_env_enabled=True, legacy_actions_enabled=True, full_actions_enabled=True)
    if mode == "world3d_sync":
        return World3DSyncWorld(seed=seed, headless_enabled=True, sync3d_enabled=True)
    if mode == "world2d_headless":
        return World2DHeadlessWorld(seed=seed, headless_enabled=True)
    if mode == "world2d_legacy_env":
        return World2DLegacyEnvWorld(seed=seed, legacy_env_enabled=True)
    if mode == "world2d_lite":
        return World2DLiteWorld(seed=seed)
    return RoomWorld()
