"""Tests Sprints 63–66 — Fase 12 (facade, motor único, Flask default)."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain
from brain.profile import DEMO_LITE_PROFILE
from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import (
    run_unified_motor_smoke_task,
    run_world_demo_facade_task,
)
from nexo.demo.flask_unified import create_unified_session, flask_unified_enabled_by_default
from nexo.demo.world_demo_facade import WorldDemoFacade
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_world_demo_facade_attaches_brain():
    brain = InfantApeBrain(
        profile=DEMO_LITE_PROFILE,
        headless=True,
        auto_save=False,
        seed=42,
    )
    brain.world.ensure_home()
    facade = WorldDemoFacade()
    facade.attach_brain(brain)
    assert facade._world2d is brain.world
    assert facade.facade_fidelity_score() > 0.0


def test_world_demo_facade_task():
    result = run_world_demo_facade_task(ablation=INTEGRATED_FULL, seed=42, ticks=25)
    assert result.task_id == "world_demo_facade"
    assert result.primary_metrics["shared_world"] == 1.0


def test_unified_motor_smoke_task():
    result = run_unified_motor_smoke_task(ablation=INTEGRATED_FULL, seed=42, ticks=20)
    assert result.task_id == "unified_motor_smoke"
    assert result.primary_metrics["motor_authority_integrated"] == 1.0


def test_flask_unified_default_on():
    assert flask_unified_enabled_by_default() is True


def test_integrated_motor_primary_session(tmp_path: Path):
    brain = InfantApeBrain(
        profile=DEMO_LITE_PROFILE,
        state_dir=tmp_path,
        headless=True,
        auto_save=False,
        seed=42,
        experiment_flags=replace(AblationFlags(), enable_neural_telemetry=True),
    )
    brain.world.ensure_home()
    session = create_unified_session(brain, _repo_root() / "configs/nexo/flask_unified_v2.yaml")
    assert session.integrated_motor_primary is True
    out = session.world_tick(steps=5)
    assert out["integrated"]["motor_authority"] == "integrated"
    assert session.runtime.clock.tick >= 5


def test_integrated_v66_yaml():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v66.yaml")
    assert rt.config.profile == "integrated_v66"
    assert rt.config.unified_motor_mode == "integrated"
    assert rt.config.world_mode == "world_demo_facade"


def test_task_registry_fase12():
    assert "world_demo_facade" in TASK_REGISTRY
    assert "unified_motor_smoke" in TASK_REGISTRY
