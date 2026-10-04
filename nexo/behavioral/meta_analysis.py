"""Meta-análisis sobre paquetes de replicación integrados."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from nexo.behavioral.event_log import summarize_event_log_payload

_NUMERIC_RESULT_KEYS = (
    "final_energy",
    "final_fatigue",
    "mean_surprise",
    "event_count",
    "trace_events",
    "memory_retrievals",
    "deliberation_events",
    "mean_dopamine",
)


def load_replication_bundle(path: Path) -> dict[str, Any] | None:
    """Carga manifest + result + resumen event_log de un directorio de replicación."""
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result: dict[str, Any] = {}
    result_path = path / "result.json"
    if result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
    event_summary: dict[str, Any] = {}
    event_log_path = path / "event_log.json"
    if event_log_path.is_file():
        payload = json.loads(event_log_path.read_text(encoding="utf-8"))
        event_summary = summarize_event_log_payload(payload)
    return {
        "dir": str(path),
        "manifest": manifest,
        "result": result,
        "event_summary": event_summary,
    }


def discover_replication_bundles(root: Path) -> list[dict[str, Any]]:
    """Encuentra paquetes con manifest.json en root o subdirectorios inmediatos."""
    if not root.is_dir():
        return []
    bundles: list[dict[str, Any]] = []
    direct = load_replication_bundle(root)
    if direct is not None:
        bundles.append(direct)
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        bundle = load_replication_bundle(child)
        if bundle is not None:
            bundles.append(bundle)
    return bundles


def _mean_std(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    mean = sum(values) / len(values)
    if len(values) < 2:
        return mean, 0.0
    var = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return mean, math.sqrt(var)


def summarize_replications(bundles: list[dict[str, Any]]) -> dict[str, Any]:
    """Resumen de consistencia entre paquetes de replicación."""
    trajectory_hashes = [
        str(b["result"].get("trajectory_hash", ""))
        for b in bundles
        if b.get("result")
    ]
    metric_fps = [
        str(b["result"].get("metric_fingerprint", ""))
        for b in bundles
        if b.get("result")
    ]
    replication_ids = [str(b["manifest"].get("replication_id", "")) for b in bundles]
    seeds = [
        b["manifest"].get("seed", b.get("result", {}).get("seed"))
        for b in bundles
    ]
    profiles = sorted({str(b["manifest"].get("profile", "")) for b in bundles if b.get("manifest")})
    non_empty_hashes = [h for h in trajectory_hashes if h]
    non_empty_fps = [f for f in metric_fps if f]

    event_type_totals: Counter[str] = Counter()
    for bundle in bundles:
        summary = bundle.get("event_summary") or {}
        for event_type, count in (summary.get("type_counts") or {}).items():
            event_type_totals[str(event_type)] += int(count)

    return {
        "n_bundles": len(bundles),
        "profiles": profiles,
        "seeds": seeds,
        "unique_replication_ids": len({r for r in replication_ids if r}),
        "unique_trajectory_hashes": len(set(non_empty_hashes)),
        "unique_metric_fingerprints": len(set(non_empty_fps)),
        "trajectory_consensus": len(set(non_empty_hashes)) <= 1 if non_empty_hashes else False,
        "metric_consensus": len(set(non_empty_fps)) <= 1 if non_empty_fps else False,
        "replication_ids": replication_ids,
        "trajectory_hashes": trajectory_hashes,
        "metric_fingerprints": metric_fps,
        "pooled_event_types": dict(event_type_totals.most_common(15)),
    }


def aggregate_numeric_metrics(bundles: list[dict[str, Any]]) -> dict[str, Any]:
    """Agrega métricas numéricas de result.json entre réplicas."""
    pooled: dict[str, list[float]] = {k: [] for k in _NUMERIC_RESULT_KEYS}
    for bundle in bundles:
        result = bundle.get("result") or {}
        for key in _NUMERIC_RESULT_KEYS:
            val = result.get(key)
            if isinstance(val, (int, float)):
                pooled[key].append(float(val))
    aggregates: dict[str, Any] = {}
    for key, values in pooled.items():
        if not values:
            continue
        mean, std = _mean_std(values)
        aggregates[key] = {
            "mean": round(mean, 6),
            "std": round(std, 6),
            "n": len(values),
        }
    return aggregates


def build_meta_analysis(
    bundles: list[dict[str, Any]],
    *,
    replication_root: str,
) -> dict[str, Any]:
    summary = summarize_replications(bundles)
    return {
        "replication_root": replication_root,
        "n_bundles": summary["n_bundles"],
        "summary": summary,
        "aggregates": aggregate_numeric_metrics(bundles),
        "bundles": [
            {
                "dir": b["dir"],
                "profile": b["manifest"].get("profile"),
                "seed": b["manifest"].get("seed", b.get("result", {}).get("seed")),
                "replication_id": b["manifest"].get("replication_id"),
                "trajectory_hash": b.get("result", {}).get("trajectory_hash"),
                "metric_fingerprint": b.get("result", {}).get("metric_fingerprint"),
                "event_summary": b.get("event_summary") or {},
            }
            for b in bundles
        ],
    }


def export_meta_analysis(
    replication_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Escanea réplicas y exporta meta-análisis JSON."""
    bundles = discover_replication_bundles(replication_root)
    payload = build_meta_analysis(
        bundles,
        replication_root=str(replication_root),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "exported": True,
        "path": str(output_path),
        "n_bundles": payload["n_bundles"],
        "trajectory_consensus": payload["summary"]["trajectory_consensus"],
        "metric_consensus": payload["summary"]["metric_consensus"],
    }
