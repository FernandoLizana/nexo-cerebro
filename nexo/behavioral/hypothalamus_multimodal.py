"""Hipotálamo multimodal integrado — puente legacy advisory (Sprint 58)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def fuse_multimodal_signals(runtime: Any) -> dict[str, float]:
    """Fusiona señales sensoriales + homeostasis en moduladores."""
    world = runtime.world
    body = runtime.body
    valence = 0.0
    arousal = 0.0
    novelty = 0.0
    if hasattr(world, "danger_level"):
        arousal = max(arousal, float(world.danger_level))
    if hasattr(world, "distractor_salience"):
        novelty = float(world.distractor_salience)
    if hasattr(world, "caregiver_present") and world.caregiver_present:
        valence += 0.2
    energy = float(getattr(body, "energy", 0.5))
    fatigue = float(getattr(body, "fatigue", 0.0))
    legacy_hypo: dict[str, float] = {}
    if runtime.legacy_brain is not None and hasattr(runtime.legacy_brain, "hypothalamus"):
        h = runtime.legacy_brain.hypothalamus
        legacy_hypo = {
            "dopamine": float(getattr(h, "dopamine", 0.4)),
            "cortisol": float(getattr(h, "cortisol", 0.2)),
            "oxytocin": float(getattr(h, "oxytocin", 0.3)),
        }
    dopamine = legacy_hypo.get("dopamine", 0.35 + novelty * 0.3 + max(valence, 0) * 0.2)
    cortisol = legacy_hypo.get("cortisol", 0.2 + arousal * 0.4 + fatigue * 0.2)
    oxytocin = legacy_hypo.get("oxytocin", 0.3 + valence * 0.25)
    return {
        "dopamine": round(min(1.0, max(0.0, dopamine)), 4),
        "cortisol": round(min(1.0, max(0.0, cortisol)), 4),
        "oxytocin": round(min(1.0, max(0.0, oxytocin)), 4),
        "energy": round(energy, 4),
        "valence": round(valence, 4),
        "arousal": round(arousal, 4),
        "novelty": round(novelty, 4),
    }


def summarize_hypothalamus_multimodal(runtime: Any) -> dict[str, Any]:
    log = runtime.state_store.event_log
    events = [ev for ev in log if ev.event_type == "hypothalamus.multimodal"]
    fused = fuse_multimodal_signals(runtime)
    mods = runtime.scheduler.config.get("modulators")
    integrated_dopa = float(getattr(mods, "dopamine", 0.0)) if mods else 0.0
    return {
        "multimodal_events": len(events),
        "fused_signals": fused,
        "integrated_dopamine": integrated_dopa,
        "legacy_hypothalamus_present": (
            runtime.legacy_brain is not None
            and hasattr(runtime.legacy_brain, "hypothalamus")
        ),
        "multimodal_score": min(1.0, len(events) / max(runtime.clock.tick, 1) * 3 + fused["dopamine"] * 0.3),
    }


def export_hypothalamus_multimodal(
    runtime: Any,
    result: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    summary = summarize_hypothalamus_multimodal(runtime)
    payload = {
        "profile": result.get("profile"),
        "seed": result.get("seed"),
        "ticks": result.get("ticks"),
        "summary": summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"exported": True, "path": str(output_path), **summary}
