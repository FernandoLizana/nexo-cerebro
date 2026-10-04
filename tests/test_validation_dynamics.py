"""Bloque K — validación científica, observatorio y guardrails (items 98–100)."""

from __future__ import annotations

from dataclasses import replace

from brain.agency_audit import audit_summary, scan_brain_agency
from brain.experiment_flags import AblationFlags
from brain.observatory_hud import build_observatory_hud
from brain.validation_dynamics import BATTERY_E1_E8, ValidationDynamicsStack


def test_battery_manifest_10k():
    stack = ValidationDynamicsStack()
    manifest = stack.battery_manifest(profile="10k", seeds=20)
    assert len(manifest["experiments"]) == 8
    ids = {row["id"] for row in manifest["experiments"]}
    assert ids == {e.experiment_id for e in BATTERY_E1_E8}
    assert manifest["profile_primary"] == "10k"
    assert manifest["seeds_recommended"] == 20


def test_smoke_battery_compact():
    stack = ValidationDynamicsStack()
    out = stack.run_smoke(seeds=2, steps=6, condition="full")
    assert out["ok"] is True
    assert len(out["summaries"]) == 2
    assert stack.last_smoke.get("condition") == "full"


def test_observatory_hud_fields():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.experiment_flags = replace(
        AblationFlags(),
        enable_observatory_hud=True,
        enable_neural_telemetry=True,
        enable_td_reward=True,
        enable_limited_wm=True,
    )
    brain.working_memory.limited = True
    hud = build_observatory_hud(brain)
    assert "causal" in hud
    assert "telemetry" in hud
    assert "td" in hud
    assert "working_memory" in hud
    assert "study_tracks" in hud
    assert hud["agency_guard"]["deliberation_selects_actions"] is True
    assert hud["agency_guard"]["observatory_selects_actions"] is False
    assert hud.get("one_liner")


def test_agency_audit_no_violations():
    violations = scan_brain_agency()
    assert violations == [], [f"{v.path}:{v.line} {v.reason}" for v in violations]


def test_agency_audit_summary_ok():
    summary = audit_summary()
    assert summary["ok"] is True
    assert summary["primary_writer"] == "brain/deliberation.py"


def test_validation_to_dict():
    stack = ValidationDynamicsStack()
    stack.run_smoke(seeds=1, steps=4)
    d = stack.to_dict()
    assert "E1" in d["battery"]
    assert d["last_smoke"]


def test_run_battery_manifest_only():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-m", "experiments.run_battery_10k", "--manifest-only", "--profile", "10k"],
        cwd=root,
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "CEREBRO_SKIP_PROCESS_GUARD": "1", "CEREBRO_OLLAMA": "0"},
    )
    assert proc.returncode == 0, proc.stderr
    assert "E1" in proc.stdout and "E8" in proc.stdout
