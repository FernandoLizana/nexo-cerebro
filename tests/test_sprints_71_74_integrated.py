"""Tests Sprints 71–74 — Fase 14 (memory unification, causal certificate, day in the life)."""

from __future__ import annotations

from pathlib import Path

from brain.mind import InfantApeBrain
from brain.profile import DEMO_LITE_PROFILE
from nexo.behavioral.causal_certificate import build_causal_certificate, summarize_causal_certificates
from nexo.behavioral.memory_unification import summarize_memory_unification
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import (
    run_causal_certificate_smoke_task,
    run_day_in_the_life_smoke_task,
    run_memory_unification_smoke_task,
)
from nexo.demo.day_in_the_life import build_day_timeline, day_in_the_life_ticks
from nexo.demo.memory_unification import promote_episode_to_legacy
from nexo.integrated_runtime import _repo_root, runtime_from_config


def test_integrated_v80_yaml():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v80.yaml")
    assert rt.config.profile == "integrated_v80"
    assert rt.config.memory_unification_mode == "integrated"
    assert rt.config.causal_certificate_mode == "integrated"
    assert rt.config.day_in_the_life_mode == "integrated"
    assert rt.clock.seconds_per_tick == 300.0


def test_promote_episode_to_legacy(tmp_path: Path):
    brain = InfantApeBrain(
        profile=DEMO_LITE_PROFILE,
        state_dir=tmp_path,
        headless=True,
        auto_save=False,
        seed=42,
    )
    episode = type(
        "Ep",
        (),
        {
            "episode_id": "ep_test",
            "event_embedding": [0.1, 0.2, 0.3],
            "confidence": 0.9,
            "affective_context": (0.2, 0.4, 0.0),
            "action": "explore",
            "outcome": "ok",
            "modality": "world",
            "body_context": (0.8, 0.1, 0.0),
        },
    )()
    out = promote_episode_to_legacy(brain, episode)
    assert out["promoted"] is True
    assert out["key"].startswith("hippo_")


def test_causal_certificate_builder():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v80.yaml")
    rt.config.ticks = 8
    rt.run()
    cert = build_causal_certificate(rt)
    assert "integrated_action" in cert
    assert "agency_contract" in cert
    summary = summarize_causal_certificates(rt)
    assert summary["certificate_events"] >= 8


def test_day_in_the_life_ticks():
    assert day_in_the_life_ticks(simulated_hours=24.0, seconds_per_tick=300.0) == 288


def test_build_day_timeline():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v80.yaml")
    rt.config.ticks = 24
    rt.run()
    timeline = build_day_timeline(rt)
    assert timeline["total_ticks"] == 24
    assert timeline["simulated_hours"] > 0.0


def test_task_registry_fase14():
    for tid in (
        "memory_unification_smoke",
        "causal_certificate_smoke",
        "day_in_the_life_smoke",
    ):
        assert tid in TASK_REGISTRY


def test_memory_unification_smoke_task():
    result = run_memory_unification_smoke_task(seed=42, ticks=40)
    assert result.task_id == "memory_unification_smoke"
    assert result.primary_metrics["unification_score"] >= 0.0


def test_causal_certificate_smoke_task():
    result = run_causal_certificate_smoke_task(seed=42, ticks=20)
    assert result.task_id == "causal_certificate_smoke"
    assert result.primary_metrics["valid_certificates"] >= 0.0


def test_day_in_the_life_smoke_task():
    result = run_day_in_the_life_smoke_task(seed=42, ticks=48)
    assert result.task_id == "day_in_the_life_smoke"
    assert result.primary_metrics["simulated_hours"] > 0.0
    assert result.primary_metrics["causal_certificates"] >= 0.0


def test_memory_unification_summary_with_brain(tmp_path: Path):
    brain = InfantApeBrain(
        profile=DEMO_LITE_PROFILE,
        state_dir=tmp_path,
        headless=True,
        auto_save=False,
        seed=42,
    )
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v80.yaml", legacy_brain=brain)
    rt.config.ticks = 30
    rt.run()
    summary = summarize_memory_unification(rt)
    assert summary["mode"] == "post_consolidation"
    assert summary["unification_score"] >= 0.0
