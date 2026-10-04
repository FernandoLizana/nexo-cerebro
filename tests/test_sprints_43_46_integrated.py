"""Tests Sprints 43–46 — peso deliberación, figuras SVG, pipeline paper, v46."""

from __future__ import annotations

import json
from pathlib import Path

from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.behavioral.battery_paper import export_battery_paper
from nexo.behavioral.deliberation_weight import (
    export_deliberation_weight,
    resolve_weighted_action,
    summarize_deliberation_weight,
)
from nexo.behavioral.paper_figures import export_paper_figures, render_bar_chart_svg
from nexo.behavioral.pipeline_paper import run_pipeline_paper
from nexo.behavioral.task_registry import TASK_REGISTRY
from nexo.behavioral.tasks import run_deliberation_weight_task
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_resolve_weighted_action_legacy_bias():
    class Ev:
        def __init__(self, tick, action, legacy=False):
            self.tick = tick
            self.event_type = "action.selected"
            self.payload = {"action": action, "legacy": legacy}

    log = [Ev(1, "explore", False), Ev(1, "eat", True)]
    low = resolve_weighted_action(log, tick=1, legacy_weight=0.0)
    high = resolve_weighted_action(log, tick=1, legacy_weight=0.7)
    assert low["resolved_action"] == "explore"
    assert high["resolved_action"] == "eat"


def test_deliberation_weight_process():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=15,
            deliberation_weight_mode="integrated",
            deliberation_unified_mode="legacy",
            legacy_advisory_weight=0.6,
            legacy_adapter_mode="integrated",
        )
    )
    rt.run()
    summary = summarize_deliberation_weight(rt)
    assert summary["legacy_weight"] == 0.6
    weighted = [ev for ev in rt.state_store.event_log if ev.event_type == "action.weighted"]
    assert len(weighted) >= 1


def test_deliberation_weight_task():
    result = run_deliberation_weight_task(ablation=INTEGRATED_FULL, seed=42, ticks=35, legacy_weight=0.6)
    assert result.task_id == "deliberation_weight_sweep"
    assert result.primary_metrics["legacy_weight"] == 0.6


def test_task_registry_weight_sweep():
    assert "deliberation_weight_sweep" in TASK_REGISTRY


def test_paper_figures_svg(tmp_path: Path):
    report = tmp_path / "r.json"
    report.write_text(
        json.dumps([
            {"task_id": "survival", "primary_metrics": {"survival_success": 0.9}},
            {"task_id": "foraging", "primary_metrics": {"forage_score": 0.5}},
        ]),
        encoding="utf-8",
    )
    meta = export_paper_figures(report, tmp_path / "fig")
    assert meta["exported"] is True
    assert (tmp_path / "fig" / "battery_scores.svg").exists()
    svg = render_bar_chart_svg({})
    assert "No data" in svg or "<svg" in svg


def test_battery_paper_list_format(tmp_path: Path):
    report = tmp_path / "list.json"
    report.write_text(
        json.dumps([{"task_id": "survival", "ablation_id": "integrated_full", "seed": 42, "primary_metrics": {"x": 1.0}}]),
        encoding="utf-8",
    )
    meta = export_battery_paper({"run": report}, tmp_path / "bp")
    assert meta["exported"] is True


def test_pipeline_paper(tmp_path: Path, monkeypatch):
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        "name: test\nversion: 1\nprofile: integrated_v46\nseeds: [42]\nablations: [integrated_full]\n"
        "lesions: [lesion_none]\ntasks: [survival]\nexport:\n  json: report.json\n",
        encoding="utf-8",
    )

    def fake_execute(path):
        out = tmp_path / "report.json"
        out.write_text(json.dumps([{"task_id": "survival", "primary_metrics": {"s": 0.8}}]), encoding="utf-8")
        return {"json": str(out)}

    monkeypatch.setattr("nexo.behavioral.manifest.execute_manifest", fake_execute)
    summary = run_pipeline_paper(manifest, output_dir=tmp_path / "pipe")
    assert "pipeline_paper" in summary
    assert (tmp_path / "pipe" / "figures" / "battery_scores.svg").exists()


def test_integrated_v46_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v46.yaml")
    result = rt.run(ticks=12)
    assert result["profile"] == "integrated_v46"
    assert result["deliberation_weight_mode"] == "integrated"
    assert result["paper_figures_mode"] == "integrated"
    assert result["pipeline_paper_mode"] == "integrated"


def test_deliberation_weight_export(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=10,
            deliberation_weight_mode="integrated",
            legacy_advisory_weight=0.5,
            legacy_adapter_mode="integrated",
        )
    )
    result = rt.run()
    out = tmp_path / "w.json"
    meta = export_deliberation_weight(rt, result, out)
    assert meta["exported"] is True
