"""Bundle de release reproducible con checksums (Sprint 50)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_artifact_checksums(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not root.is_dir():
        return out
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            out[rel] = _sha256(path)
    return out


def build_reproduce_text(profile: str, config_path: str) -> str:
    return "\n".join([
        "NEXO Integrated Brain — Reproducibility",
        f"Profile: {profile}",
        "",
        "Commands:",
        f"  python -m nexo.run --config {config_path} --ticks 18",
        "  python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v12_mini.yaml",
        "  python -m pytest tests/test_sprints_47_50_integrated.py -q",
        "",
    ])


def export_release_bundle(
    result: dict[str, Any],
    output_dir: Path,
    *,
    artifact_roots: dict[str, Path] | None = None,
    config_path: str = "configs/nexo/integrated_v50.yaml",
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = str(result.get("profile", "integrated"))
    checksums: dict[str, dict[str, str]] = {}
    for name, root in (artifact_roots or {}).items():
        if root.is_dir():
            checksums[name] = collect_artifact_checksums(root)
    reproduce = build_reproduce_text(profile, config_path)
    (output_dir / "REPRODUCE.txt").write_text(reproduce, encoding="utf-8")
    manifest = {
        "profile": profile,
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "replication_id": result.get("replication_id"),
        "trajectory_hash": result.get("trajectory_hash"),
        "metric_fingerprint": result.get("metric_fingerprint"),
        "config_path": config_path,
        "checksums": checksums,
    }
    manifest_path = output_dir / "release_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "exported": True,
        "output_dir": str(output_dir),
        "manifest": str(manifest_path),
        "reproduce_txt": str(output_dir / "REPRODUCE.txt"),
        "n_artifact_roots": len(checksums),
        "n_files": sum(len(v) for v in checksums.values()),
    }
