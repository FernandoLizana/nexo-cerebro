"""Bundle de publicación reproducible end-to-end (Sprint 34)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from nexo.behavioral.replication import _MODE_FIELDS, config_fingerprint


def build_publication_manifest(runtime: Any, result: dict[str, Any]) -> dict[str, Any]:
    cfg = runtime.config
    modes = {
        k: getattr(cfg, k)
        for k in _MODE_FIELDS
        if k not in ("profile", "seed", "ticks") and hasattr(cfg, k)
    }
    return {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "config_fingerprint": config_fingerprint(cfg),
        "trajectory_hash": result.get("trajectory_hash"),
        "metric_fingerprint": result.get("metric_fingerprint"),
        "replication_id": result.get("replication_id"),
        "modes": modes,
        "lesion_profile": cfg.lesion_profile,
    }


def export_publication_bundle(
    runtime: Any,
    result: dict[str, Any],
    output_dir: Path,
    *,
    artifact_paths: dict[str, Path] | None = None,
    include_paper_pack: bool = False,
    paper_pack_dir: Path | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_publication_manifest(runtime, result)
    (output_dir / "publication_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "config_snapshot.yaml").write_text(
        yaml.safe_dump(
            {
                "profile": runtime.config.profile,
                "seed": runtime.config.seed,
                "ticks": runtime.config.ticks,
                "modes": manifest["modes"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    copied: dict[str, str] = {}
    for name, src in (artifact_paths or {}).items():
        if src.is_file():
            dest = output_dir / src.name
            shutil.copy2(src, dest)
            copied[name] = str(dest)
    if include_paper_pack and paper_pack_dir is not None and paper_pack_dir.is_dir():
        paper_dest = output_dir / "paper_pack"
        if paper_dest.exists():
            shutil.rmtree(paper_dest)
        shutil.copytree(paper_pack_dir, paper_dest)
        copied["paper_pack"] = str(paper_dest)
    summary = {
        "exported": True,
        "output_dir": str(output_dir),
        "config_fingerprint": manifest["config_fingerprint"],
        "artifacts_copied": copied,
    }
    (output_dir / "bundle_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return summary


def export_full_publication_bundle(
    runtime: Any,
    result: dict[str, Any],
    output_dir: Path,
    *,
    artifact_paths: dict[str, Path] | None = None,
    paper_pack_dir: Path | None = None,
    battery_paper_dir: Path | None = None,
    figures_dir: Path | None = None,
) -> dict[str, Any]:
    """Bundle completo paper: publicación + paper_pack + battery_paper + figures."""
    output_dir.mkdir(parents=True, exist_ok=True)
    base = export_publication_bundle(
        runtime,
        result,
        output_dir,
        artifact_paths=artifact_paths,
        include_paper_pack=paper_pack_dir is not None,
        paper_pack_dir=paper_pack_dir,
    )
    copied = dict(base.get("artifacts_copied") or {})
    if battery_paper_dir is not None and battery_paper_dir.is_dir():
        dest = output_dir / "battery_paper"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(battery_paper_dir, dest)
        copied["battery_paper"] = str(dest)
    if figures_dir is not None and figures_dir.is_dir():
        dest = output_dir / "figures"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(figures_dir, dest)
        copied["figures"] = str(dest)
    full_summary = {
        **base,
        "full_publication": True,
        "artifacts_copied": copied,
    }
    (output_dir / "full_bundle_summary.json").write_text(
        json.dumps(full_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return full_summary
