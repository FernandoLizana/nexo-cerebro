"""Sesión Flask unificada — InfantApeBrain + IntegratedRuntime (Fase 11–12)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from nexo.behavioral.flask_demo_bridge import build_flask_bridge_payload, summarize_flask_demo_bridge
from nexo.behavioral.unified_motor import summarize_unified_motor
from nexo.behavioral.agent_loop_sync import summarize_agent_loop_sync
from nexo.behavioral.memory_bridge import summarize_memory_bridge
from nexo.demo.agent_loop_sync import run_agent_loop_lite_sync
from nexo.demo.legacy_sync import (
    sync_integrated_body_from_legacy,
    sync_legacy_body_from_integrated,
    sync_legacy_deliberation_from_integrated,
)
from nexo.demo.memory_bridge import sync_memory_bridge_advisory
from nexo.demo.world3d_sync import bind_legacy_world, extract_game3d_state, game3d_fidelity_score
from nexo.integrated_runtime import IntegratedRuntime, _repo_root, runtime_from_config


def default_unified_config_path() -> Path:
    env = os.environ.get("NEXO_FLASK_UNIFIED_CONFIG", "").strip()
    if env:
        p = Path(env)
        return p if p.is_absolute() else _repo_root() / p
    return _repo_root() / "configs/nexo/flask_unified_v4.yaml"


def flask_unified_enabled_by_default() -> bool:
    if os.environ.get("NEXO_FLASK_LEGACY", "0").strip().lower() in ("1", "true", "yes"):
        return False
    return os.environ.get("NEXO_FLASK_UNIFIED", "1").strip().lower() in ("1", "true", "yes")


def create_unified_session(brain: Any, config_path: Path | None = None) -> FlaskUnifiedSession:
    path = config_path or default_unified_config_path()
    runtime = runtime_from_config(path, legacy_brain=brain)
    sync_integrated_body_from_legacy(brain, runtime)
    session = FlaskUnifiedSession(brain=brain, runtime=runtime, config_path=path)
    session.bind_worlds()
    return session


class FlaskUnifiedSession:
    """Puente runtime unificado: legacy o integrado como motor primario."""

    def __init__(self, *, brain: Any, runtime: Any, config_path: Path) -> None:
        self.brain = brain
        self.runtime = runtime
        self.config_path = config_path
        self._tick_count = 0

    @property
    def integrated_motor_primary(self) -> bool:
        return getattr(self.runtime.config, "unified_motor_mode", "legacy") == "integrated"

    def bind_worlds(self) -> None:
        bind_legacy_world(self.runtime, self.brain)

    def _integrated_block(self, sidecar: dict[str, Any]) -> dict[str, Any]:
        motor = summarize_unified_motor(self.runtime)
        return {
            "unified": True,
            "motor_authority": "integrated" if self.integrated_motor_primary else "legacy",
            "profile": self.runtime.config.profile,
            "config_path": str(self.config_path),
            "trajectory_hash": sidecar.get("trajectory_hash"),
            "integrated_ticks": sidecar.get("ticks"),
            "bridge": build_flask_bridge_payload(self.runtime),
            "game3d_fidelity": game3d_fidelity_score(extract_game3d_state(self.runtime.world)),
            "unified_motor": motor,
        }

    def _build_tick_response(self, sidecar: dict[str, Any]) -> dict[str, Any]:
        sync_legacy_deliberation_from_integrated(self.brain, self.runtime)
        sync_legacy_body_from_integrated(self.brain, self.runtime)
        agent_loop_sync: dict[str, Any] = {"synced": False}
        memory_bridge: dict[str, Any] = {"synced": False}
        if self.integrated_motor_primary and getattr(
            self.runtime.config, "agent_loop_sync_mode", "legacy"
        ) == "integrated":
            agent_loop_sync = run_agent_loop_lite_sync(self.brain)
        if getattr(self.runtime.config, "memory_bridge_mode", "legacy") == "integrated":
            memory_bridge = sync_memory_bridge_advisory(self.brain, self.runtime)
        from brain.causal_hud import build_causal_hud

        out = self.brain.snapshot()
        out["world"] = self.brain._world_dict()
        out["deliberation"] = self.brain.deliberation.last.to_dict()
        out["body"] = self.brain._body_snapshot() if hasattr(self.brain, "_body_snapshot") else self.brain.body.to_dict()
        out["causal_hud"] = build_causal_hud(self.brain)
        out["integrated"] = self._integrated_block(sidecar)
        out["integrated"]["agent_loop_sync"] = agent_loop_sync
        out["integrated"]["memory_bridge"] = memory_bridge
        return out

    def world_tick(self, *, steps: int = 1) -> dict[str, Any]:
        steps = max(1, min(int(steps), 500))
        if self.integrated_motor_primary:
            sidecar: dict[str, Any] = {}
            for _ in range(steps):
                self.bind_worlds()
                sidecar = self.runtime.run(1)
            self._tick_count += steps
            return self._build_tick_response(sidecar)
        out = self.brain.world_tick(steps=steps)
        self.bind_worlds()
        sidecar = self.runtime.run_sidecar(steps)
        self._tick_count += steps
        out["integrated"] = self._integrated_block(sidecar)
        return out

    def world_dict(self) -> dict[str, Any]:
        self.bind_worlds()
        d = self.brain._world_dict()
        d["integrated"] = {
            "unified": True,
            "motor_authority": "integrated" if self.integrated_motor_primary else "legacy",
            "profile": self.runtime.config.profile,
            "bridge": build_flask_bridge_payload(self.runtime),
            "game3d": extract_game3d_state(self.runtime.world),
        }
        return d

    def snapshot(self) -> dict[str, Any]:
        self.bind_worlds()
        snap = self.brain.snapshot()
        snap["integrated"] = self.status()
        return snap

    def language_status(self) -> dict[str, Any]:
        return {
            **self.brain.language.status(),
            "network": self.brain.language_network.status(self.brain),
            "integrated": {"unified": True, "profile": self.runtime.config.profile},
        }

    def time_state(self) -> dict[str, Any]:
        state = self.brain.time_state()
        state["integrated_ticks"] = self.runtime.clock.tick
        return state

    def status(self) -> dict[str, Any]:
        self.bind_worlds()
        bridge = summarize_flask_demo_bridge(self.runtime)
        return {
            "unified": True,
            "profile": self.runtime.config.profile,
            "config_path": str(self.config_path),
            "flask_unified_mode": getattr(self.runtime.config, "flask_unified_mode", "legacy"),
            "unified_motor_mode": getattr(self.runtime.config, "unified_motor_mode", "legacy"),
            "motor_authority": "integrated" if self.integrated_motor_primary else "legacy",
            "legacy_ticks": self._tick_count,
            "integrated_clock": self.runtime.clock.tick,
            "bridge_summary": bridge,
            "game3d_fidelity": game3d_fidelity_score(extract_game3d_state(self.runtime.world)),
            "unified_motor": summarize_unified_motor(self.runtime),
            "agent_loop_sync": summarize_agent_loop_sync(self.runtime),
            "memory_bridge": summarize_memory_bridge(self.runtime),
        }

    def causal_hud_overlay(self) -> dict[str, Any]:
        return {
            "integrated_unified": True,
            "integrated_profile": self.runtime.config.profile,
            "integrated_ticks": self.runtime.clock.tick,
            "motor_authority": "integrated" if self.integrated_motor_primary else "legacy",
        }
