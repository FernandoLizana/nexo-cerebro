"""Paquetes de replicación reproducibles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

_MODE_FIELDS = (
    "profile", "seed", "ticks",
    "perception_mode", "memory_mode", "executive_mode", "learning_mode",
    "consciousness_mode", "social_mode", "sleep_mode", "evaluation_mode",
    "intervention_mode", "lesion_profile", "latency_mode", "analysis_mode",
    "routing_mode", "statistics_mode", "tracing_mode", "replication_mode",
    "permutation_mode",
    "correction_mode",
    "eventlog_mode",
    "meta_analysis_mode",
    "replication_batch_mode",
    "cross_battery_mode",
    "phenomenology_mode",
    "legacy_bridge_mode",
    "world_mode",
    "inference_mode",
    "orchestration_mode",
    "legacy_adapter_mode",
    "scale_mode",
    "hierarchical_inference_mode",
    "deliberation_bridge_mode",
    "deliberation_fusion_mode",
    "deliberation_unified_mode",
    "world2d_legacy_actions_mode",
    "world2d_full_actions_mode",
    "world2d_legacy_env_mode",
    "lif_scale_mode",
    "gpu_bench_mode",
    "publication_mode",
    "paper_pack_mode",
    "battery_paper_mode",
    "full_publication_mode",
    "deliberation_weight_mode",
    "paper_figures_mode",
    "pipeline_paper_mode",
    "latex_master_mode",
    "battery_full_mode",
    "release_bundle_mode",
    "legacy_adapter_early_mode",
    "world2d_headless_mode",
    "roadmap100_bridge_mode",
    "flask_demo_bridge_mode",
    "world3d_sync_mode",
    "autonomy_guard_mode",
    "hypothalamus_multimodal_mode",
    "companion_integrated_mode",
    "flask_unified_mode",
    "unified_motor_mode",
    "agent_loop_sync_mode",
    "memory_bridge_mode",
    "flask_study_proxy_mode",
    "roadmap100_e_block_mode",
    "memory_unification_mode",
    "causal_certificate_mode",
    "day_in_the_life_mode",
    "agency_audit_mode",
    "science_bundle_mode",
)


def config_fingerprint(cfg: Any) -> str:
    payload = {k: getattr(cfg, k, None) for k in _MODE_FIELDS}
    payload["legacy_advisory_weight"] = getattr(cfg, "legacy_advisory_weight", 0.0)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def build_replication_bundle(
    runtime: Any,
    result: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    """Exporta result + trace + config en directorio reproducible."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cfg = runtime.config
    rep_id = config_fingerprint(cfg)
    manifest = {
        "replication_id": rep_id,
        "profile": cfg.profile,
        "seed": cfg.seed,
        "ticks": result.get("ticks"),
        "trajectory_hash": result.get("trajectory_hash"),
        "metric_fingerprint": result.get("metric_fingerprint", ""),
        "replication_mode": getattr(cfg, "replication_mode", "legacy"),
    }
    (output_dir / "result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (output_dir / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "profile": cfg.profile,
                "seed": cfg.seed,
                "ticks": cfg.ticks,
                "replication_id": rep_id,
                "modes": {
                    k: getattr(cfg, k)
                    for k in _MODE_FIELDS
                    if k not in ("profile", "seed", "ticks", "lesion_profile")
                },
                "lesion_profile": cfg.lesion_profile,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    trace_meta = runtime.export_trace(output_dir / "trace.json")
    eventlog_meta: dict[str, Any] = {"exported": False}
    if getattr(cfg, "eventlog_mode", "legacy") == "integrated":
        from nexo.behavioral.event_log import export_event_log

        eventlog_meta = export_event_log(runtime, output_dir / "event_log.json")
    phenom_meta: dict[str, Any] = {"exported": False}
    if getattr(cfg, "phenomenology_mode", "legacy") == "integrated":
        from nexo.behavioral.phenomenology import export_phenomenology

        phenom_meta = export_phenomenology(runtime, output_dir / "phenomenology.json")
    (output_dir / "manifest.json").write_text(
        json.dumps(
            {
                **manifest,
                "trace_export": trace_meta,
                "eventlog_export": eventlog_meta,
                "phenomenology_export": phenom_meta,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return {"replication_id": rep_id, "output_dir": str(output_dir), "manifest": manifest}
