"""Tests Sprints 67–70 — Fase 13 (agent_loop sync, memory bridge, study proxy)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain
from brain.profile import DEMO_LITE_PROFILE
from nexo.behavioral.roadmap100_e_block import ROADMAP100_E_BLOCK_IDS, audit_e_block_conditions
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import (
    run_agent_loop_sync_smoke_task,
    run_flask_study_proxy_smoke_task,
    run_memory_bridge_smoke_task,
    run_roadmap100_e_block_smoke_task,
)
from nexo.demo.agent_loop_sync import run_agent_loop_lite_sync
from nexo.demo.flask_study_proxy import wrap_study_response
from nexo.demo.flask_unified import create_unified_session
from nexo.demo.memory_bridge import sync_memory_bridge_advisory
from nexo.integrated_runtime import _repo_root, runtime_from_config


def test_agent_loop_lite_sync():
    brain = InfantApeBrain(
        profile=DEMO_LITE_PROFILE,
        headless=True,
        auto_save=False,
        seed=42,
    )
    brain.world.ensure_home()
    brain.ensure_companion()
    out = run_agent_loop_lite_sync(brain)
    assert out["synced"] is True
    assert "think" in out["phases"]


def test_memory_bridge_advisory():
    brain = InfantApeBrain(
        profile=DEMO_LITE_PROFILE,
        headless=True,
        auto_save=False,
        seed=42,
    )
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v70.yaml", legacy_brain=brain)
    stats = sync_memory_bridge_advisory(brain, rt)
    assert stats["bridge_mode"] == "advisory"
    assert "parity_ratio" in stats


def test_flask_study_proxy_overlay():
    brain = InfantApeBrain(
        profile=DEMO_LITE_PROFILE,
        headless=True,
        auto_save=False,
        seed=42,
    )
    brain.world.ensure_home()
    session = create_unified_session(brain, _repo_root() / "configs/nexo/flask_unified_v3.yaml")
    wrapped = wrap_study_response(session, {"studied": {"title": "test"}}, track="curriculum")
    assert wrapped["integrated_study"]["unified"] is True
    assert wrapped["integrated_study"]["track"] == "curriculum"


def test_integrated_v70_yaml():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v70.yaml")
    assert rt.config.profile == "integrated_v70"
    assert rt.config.agent_loop_sync_mode == "integrated"
    assert rt.config.memory_bridge_mode == "integrated"
    assert rt.config.flask_study_proxy_mode == "integrated"


def test_roadmap100_e_block_catalog():
    audit = audit_e_block_conditions()
    assert audit["catalog_size"] == len(ROADMAP100_E_BLOCK_IDS)
    assert audit["resolved_count"] == 8
    assert audit["coverage"] == 1.0


def test_task_registry_fase13():
    for tid in (
        "agent_loop_sync_smoke",
        "memory_bridge_smoke",
        "flask_study_proxy_smoke",
        "roadmap100_e_block_smoke",
    ):
        assert tid in TASK_REGISTRY


def test_agent_loop_sync_smoke_task():
    result = run_agent_loop_sync_smoke_task(seed=42, ticks=12)
    assert result.task_id == "agent_loop_sync_smoke"
    assert result.primary_metrics["sync_score"] >= 0.0


def test_memory_bridge_smoke_task():
    result = run_memory_bridge_smoke_task(seed=42, ticks=20)
    assert result.task_id == "memory_bridge_smoke"
    assert result.primary_metrics["bridge_events"] >= 0.0


def test_flask_study_proxy_smoke_task():
    result = run_flask_study_proxy_smoke_task(seed=42)
    assert result.task_id == "flask_study_proxy_smoke"
    assert result.primary_metrics["study_proxy"] == 1.0


def test_roadmap100_e_block_smoke_task():
    result = run_roadmap100_e_block_smoke_task(seed=42, ticks=30)
    assert result.task_id == "roadmap100_e_block_smoke"
    assert result.primary_metrics["e_block_score"] == 1.0


def test_unified_session_agent_loop_on_tick(tmp_path: Path):
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
    session = create_unified_session(brain, _repo_root() / "configs/nexo/flask_unified_v3.yaml")
    out = session.world_tick(steps=3)
    lite = (out.get("integrated") or {}).get("agent_loop_sync") or {}
    assert lite.get("synced") is True
    assert lite.get("thought_len", 0) >= 0
