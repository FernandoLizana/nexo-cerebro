"""Tests Sprints 47–50 — LaTeX maestro, batería full, pipeline auto, release."""

from __future__ import annotations

import json
from pathlib import Path

from nexo.ablation.profiles import INTEGRATED_FULL
from nexo.behavioral.battery_full import run_battery_full
from nexo.behavioral.latex_master import build_latex_master_body, export_latex_master
from nexo.behavioral.pipeline_paper import run_pipeline_paper_auto
from nexo.behavioral.release_bundle import export_release_bundle
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config


def test_build_latex_master_body():
    body = build_latex_master_body(profile="test_v50")
    assert "\\documentclass" in body
    assert "\\end{document}" in body


def test_export_latex_master(tmp_path: Path):
    paper = tmp_path / "paper"
    paper.mkdir()
    (paper / "metrics_table.tex").write_text("\\begin{tabular}{ll} a & b \\\\ \\end{tabular}", encoding="utf-8")
    result = {"profile": "test_v50", "seed": 42, "ticks": 10}
    meta = export_latex_master(result, tmp_path / "latex", paper_pack_dir=paper)
    assert meta["exported"] is True
    assert (tmp_path / "latex" / "nexo_integrated_master.tex").exists()


def test_release_bundle_checksums(tmp_path: Path):
    src = tmp_path / "artifacts"
    src.mkdir()
    (src / "a.txt").write_text("hello", encoding="utf-8")
    result = {"profile": "test_v50", "seed": 42, "ticks": 5, "replication_id": "abc"}
    meta = export_release_bundle(result, tmp_path / "rel", artifact_roots={"artifacts": src})
    assert meta["exported"] is True
    assert (tmp_path / "rel" / "REPRODUCE.txt").exists()
    manifest = json.loads((tmp_path / "rel" / "release_manifest.json").read_text(encoding="utf-8"))
    assert "checksums" in manifest


def test_battery_full_mini(tmp_path: Path, monkeypatch):
    manifest = tmp_path / "m.yaml"
    manifest.write_text(
        "name: t\nversion: 1\nprofile: integrated_v50\nseeds: [42]\n"
        "ablations: [integrated_full]\nlesions: [lesion_none]\n"
        "tasks: [survival]\nexport:\n  json: r.json\n  statistics: s.json\n",
        encoding="utf-8",
    )

    def fake_execute(path):
        out = tmp_path / "r.json"
        out.write_text("[]", encoding="utf-8")
        stats = tmp_path / "s.json"
        stats.write_text("{}", encoding="utf-8")
        return {
            "json": str(out),
            "statistics": str(stats),
            "total_runs": 1,
            "fdr_correction": True,
            "statistics_effects": 0,
        }

    monkeypatch.setattr("nexo.behavioral.manifest.execute_manifest", fake_execute)
    meta = run_battery_full(manifest, tmp_path / "bf")
    assert meta["exported"] is True
    assert meta["fdr_correction"] is True


def test_pipeline_paper_auto_with_latex(tmp_path: Path, monkeypatch):
    manifest = tmp_path / "m.yaml"
    manifest.write_text(
        "name: t\nversion: 1\nprofile: integrated_v50\nseeds: [42]\n"
        "ablations: [integrated_full]\nlesions: [lesion_none]\n"
        "tasks: [survival]\nexport:\n  json: report.json\n",
        encoding="utf-8",
    )

    def fake_execute(path):
        out = tmp_path / "report.json"
        out.write_text(json.dumps([{"task_id": "survival", "primary_metrics": {"s": 0.9}}]), encoding="utf-8")
        return {"json": str(out)}

    monkeypatch.setattr("nexo.behavioral.manifest.execute_manifest", fake_execute)
    summary = run_pipeline_paper_auto(
        manifest_path=manifest,
        output_dir=tmp_path / "pipe",
        result={"profile": "integrated_v50", "seed": 42, "ticks": 8},
        build_latex=True,
    )
    assert "latex_master" in summary
    assert (tmp_path / "pipe" / "latex_master" / "nexo_integrated_master.tex").exists()


def test_integrated_v50_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v50.yaml")
    result = rt.run(ticks=10)
    assert result["profile"] == "integrated_v50"
    assert result["latex_master_mode"] == "integrated"
    assert result["release_bundle_mode"] == "integrated"


def test_runtime_export_latex_master(tmp_path: Path):
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(seed=42, ticks=8, latex_master_mode="integrated", paper_pack_mode="integrated")
    )
    result = rt.run()
    paper = tmp_path / "paper"
    rt.export_paper_pack(result, paper)
    meta = rt.export_latex_master(result, tmp_path / "lm", paper_pack_dir=paper)
    assert meta["exported"] is True
