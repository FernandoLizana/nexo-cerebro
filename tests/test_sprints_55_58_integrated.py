"""Tests Sprints 55–58 — Flask bridge, 3D sync, autonomía, Nira integrada."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.behavioral.autonomy_guard import export_autonomy_guard, summarize_autonomy_guard, verify_app_autonomy_routes
from nexo.behavioral.companion_integrated import export_companion_integrated, summarize_companion_integrated
from nexo.behavioral.flask_demo_bridge import export_flask_demo_bridge, summarize_flask_demo_bridge
from nexo.behavioral.hypothalamus_multimodal import export_hypothalamus_multimodal, summarize_hypothalamus_multimodal
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import (
    run_autonomy_contract_audit_task,
    run_companion_dyad_smoke_task,
    run_flask_demo_smoke_task,
    run_hypothalamus_multimodal_smoke_task,
    run_world3d_state_sync_task,
)
from nexo.behavioral.world3d_sync_report import export_world3d_sync, summarize_world3d_sync
from nexo.core.process_autonomy_guard import AutonomyGuardProcess
from nexo.core.process_companion_integrated import CompanionIntegratedProcess
from nexo.core.process_flask_demo_bridge import FlaskDemoBridgeProcess
from nexo.core.process_hypothalamus_multimodal import HypothalamusMultimodalProcess
from nexo.demo.world3d_sync import World3DSyncWorld, game3d_fidelity_score
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_flask_demo_bridge_process():
    proc = FlaskDemoBridgeProcess()
    assert proc.process_id == "flask_demo_bridge"
    assert proc.period_ticks == 6


def test_world3d_sync_world():
    world = World3DSyncWorld(seed=42, sync3d_enabled=True)
    state = world.game3d_state()
    assert "furniture" in state
    assert game3d_fidelity_score(state) > 0.5


@pytest.mark.slow
def test_flask_demo_smoke_task():
    result = run_flask_demo_smoke_task(ablation=INTEGRATED_FULL, seed=42, ticks=12)
    assert result.task_id == "flask_demo_smoke"
    assert result.primary_metrics["bridge_score"] >= 0.0


@pytest.mark.slow
def test_world3d_state_sync_task():
    result = run_world3d_state_sync_task(ablation=INTEGRATED_FULL, seed=42, ticks=12)
    assert result.task_id == "world3d_state_sync"
    assert result.primary_metrics["fidelity"] > 0.0


@pytest.mark.slow
def test_autonomy_contract_audit_task():
    result = run_autonomy_contract_audit_task(ablation=INTEGRATED_FULL, seed=42, ticks=12)
    assert result.task_id == "autonomy_contract_audit"
    assert result.primary_metrics["app_audit_score"] > 0.0


@pytest.mark.slow
def test_hypothalamus_multimodal_smoke_task():
    result = run_hypothalamus_multimodal_smoke_task(ablation=INTEGRATED_FULL, seed=42, ticks=12)
    assert result.task_id == "hypothalamus_multimodal_smoke"
    assert result.primary_metrics["multimodal_events"] >= 0.0


@pytest.mark.slow
def test_companion_dyad_smoke_task():
    result = run_companion_dyad_smoke_task(ablation=INTEGRATED_FULL, seed=42, ticks=12)
    assert result.task_id == "companion_dyad_smoke"
    assert result.primary_metrics["bond"] >= 0.0


def test_task_registry_fase10():
    for task_id in (
        "flask_demo_smoke",
        "world3d_state_sync",
        "autonomy_contract_audit",
        "hypothalamus_multimodal_smoke",
        "companion_dyad_smoke",
    ):
        assert task_id in TASK_REGISTRY


def test_verify_app_autonomy_routes():
    audit = verify_app_autonomy_routes()
    assert audit["routes_checked"] >= 5
    assert audit["audit_score"] >= 0.5


@pytest.mark.slow
def test_runtime_fase10_exports(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=10,
            world_mode="world3d_sync",
            legacy_adapter_mode="integrated",
            flask_demo_bridge_mode="integrated",
            world3d_sync_mode="integrated",
            autonomy_guard_mode="integrated",
            hypothalamus_multimodal_mode="integrated",
            companion_integrated_mode="integrated",
        )
    )
    result = rt.run()
    assert export_flask_demo_bridge(rt, result, tmp_path / "flask.json")["exported"] is True
    assert export_world3d_sync(rt, result, tmp_path / "w3d.json")["exported"] is True
    assert export_autonomy_guard(rt, result, tmp_path / "auto.json")["exported"] is True
    assert export_hypothalamus_multimodal(rt, result, tmp_path / "hypo.json")["exported"] is True
    assert export_companion_integrated(rt, result, tmp_path / "comp.json")["exported"] is True


@pytest.mark.slow
def test_integrated_v58_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v58.yaml")
    result = rt.run(ticks=8)
    assert result["profile"] == "integrated_v58"
    assert result["flask_demo_bridge_mode"] == "integrated"
    assert result["world3d_sync_mode"] == "integrated"
    assert result["autonomy_guard_mode"] == "integrated"
    assert result["companion_integrated_mode"] == "integrated"


def test_fase10_process_priorities():
    assert AutonomyGuardProcess().priority == 62
    assert HypothalamusMultimodalProcess().period_ticks == 3
    assert CompanionIntegratedProcess().process_id == "companion_integrated"


@pytest.mark.slow
def test_summaries_after_run():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=10,
            legacy_adapter_mode="integrated",
            flask_demo_bridge_mode="integrated",
            world3d_sync_mode="integrated",
            world_mode="world3d_sync",
            autonomy_guard_mode="integrated",
            hypothalamus_multimodal_mode="integrated",
            companion_integrated_mode="integrated",
        )
    )
    rt.run()
    assert summarize_flask_demo_bridge(rt)["legacy_brain_attached"] is True
    assert summarize_world3d_sync(rt)["fidelity"] > 0.0
    assert summarize_autonomy_guard(rt)["guard_events"] >= 0
    assert summarize_hypothalamus_multimodal(rt)["multimodal_events"] >= 0
    assert summarize_companion_integrated(rt)["companion_name"] == "Nira"
