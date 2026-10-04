"""Tests Fase 11 — Flask unificado con IntegratedRuntime sidecar."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from flask import Flask, jsonify

from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE, DEMO_LITE_PROFILE
from nexo.demo.flask_unified import create_unified_session
from nexo.demo.world3d_sync import bind_legacy_world
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root


def _lite_brain(tmp_path: Path) -> InfantApeBrain:
    brain = InfantApeBrain(
        profile=DEMO_LITE_PROFILE,
        state_dir=tmp_path,
        headless=True,
        auto_save=False,
        seed=42,
        experiment_flags=replace(AblationFlags(), enable_neural_telemetry=True),
    )
    brain.world.ensure_home()
    brain.ensure_companion()
    return brain


def test_bind_legacy_world_shares_instance(tmp_path: Path):
    brain = _lite_brain(tmp_path)
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=10,
            world_mode="world3d_sync",
            legacy_adapter_mode="integrated",
            flask_unified_mode="integrated",
        ),
        legacy_brain=brain,
    )
    bind_legacy_world(rt, brain)
    assert rt.world._world2d is brain.world


def test_unified_session_world_tick(tmp_path: Path):
    brain = _lite_brain(tmp_path)
    session = create_unified_session(brain, _repo_root() / "configs/nexo/flask_unified_v2.yaml")
    out = session.world_tick(steps=5)
    assert "integrated" in out
    assert out["integrated"]["unified"] is True
    assert out["integrated"]["game3d_fidelity"] > 0.0
    assert session.runtime.clock.tick >= 5


def test_unified_session_world_dict(tmp_path: Path):
    brain = _lite_brain(tmp_path)
    session = create_unified_session(brain, _repo_root() / "configs/nexo/flask_unified_v2.yaml")
    d = session.world_dict()
    assert "agent" in d
    assert d["integrated"]["unified"] is True
    assert "game3d" in d["integrated"]


def test_run_sidecar_runs_integrated_audit(tmp_path: Path):
    brain = _lite_brain(tmp_path)
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=8,
            legacy_adapter_mode="integrated",
            legacy_adapter_early_mode="integrated",
            flask_unified_mode="integrated",
        ),
        legacy_brain=brain,
    )
    bind_legacy_world(rt, brain)
    brain.world_tick(steps=3)
    result = rt.run_sidecar(3)
    assert result["ticks"] >= 3
    assert result.get("flask_unified_mode") == "integrated"


def test_flask_unified_routes_minimal(tmp_path: Path, monkeypatch):
    brain = _lite_brain(tmp_path)
    session = create_unified_session(brain, _repo_root() / "configs/nexo/flask_unified_v2.yaml")
    app = Flask(__name__)

    @app.get("/api/world")
    def world():
        return jsonify(session.world_dict())

    @app.post("/api/world/tick")
    def tick():
        return jsonify(session.world_tick(steps=2))

    @app.get("/api/integrated/status")
    def status():
        return jsonify(session.status())

    client = app.test_client()
    r = client.get("/api/world")
    assert r.status_code == 200
    assert r.get_json()["integrated"]["unified"] is True
    r2 = client.post("/api/world/tick", json={"steps": 2})
    assert r2.status_code == 200
    assert "integrated" in r2.get_json()
    r3 = client.get("/api/integrated/status")
    assert r3.get_json()["unified"] is True


def test_integrated_v62_yaml_has_flask_unified_mode():
    from nexo.integrated_runtime import runtime_from_config

    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v62.yaml")
    assert rt.config.flask_unified_mode == "integrated"
    assert rt.config.profile == "integrated_v62"
