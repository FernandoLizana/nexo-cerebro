"""Comparación integrado vs legacy headless (Sprint 23)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def run_legacy_trajectory(*, seed: int = 42, ticks: int = 40) -> dict[str, Any]:
    """Ejecuta InfantApeBrain headless y captura choice_key por tick."""
    from brain.mind import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE, headless=True, auto_save=False, seed=seed)
    actions: list[str] = []
    for _ in range(ticks):
        out = brain.world_tick(steps=1)
        delib = out.get("deliberation") or {}
        actions.append(str(delib.get("choice_key") or ""))
    raw = json.dumps(actions, sort_keys=False).encode()
    return {
        "mode": "legacy",
        "seed": seed,
        "ticks": ticks,
        "actions": actions,
        "trajectory_hash": hashlib.sha256(raw).hexdigest(),
    }


def compare_integrated_legacy(
    integrated_result: dict[str, Any],
    legacy: dict[str, Any],
) -> dict[str, Any]:
    integrated_actions = list(integrated_result.get("actions_taken") or [])
    legacy_actions = list(legacy.get("actions") or [])
    n = max(len(integrated_actions), len(legacy_actions), 1)
    overlap = sum(
        1 for i in range(min(len(integrated_actions), len(legacy_actions)))
        if integrated_actions[i] == legacy_actions[i]
    )
    integrated_set = set(integrated_actions)
    legacy_set = set(a for a in legacy_actions if a)
    jaccard = (
        len(integrated_set & legacy_set) / len(integrated_set | legacy_set)
        if integrated_set | legacy_set
        else 0.0
    )
    return {
        "integrated_ticks": len(integrated_actions),
        "legacy_ticks": len(legacy_actions),
        "action_overlap_ratio": round(overlap / n, 6),
        "action_jaccard": round(jaccard, 6),
        "integrated_trajectory_hash": integrated_result.get("trajectory_hash"),
        "legacy_trajectory_hash": legacy.get("trajectory_hash"),
        "hash_match": integrated_result.get("trajectory_hash") == legacy.get("trajectory_hash"),
        "integrated_unique_actions": sorted(integrated_set),
        "legacy_unique_actions": sorted(legacy_set),
    }


def export_legacy_bridge(
    integrated_result: dict[str, Any],
    *,
    seed: int,
    ticks: int,
    output_path: Path,
) -> dict[str, Any]:
    legacy = run_legacy_trajectory(seed=seed, ticks=ticks)
    payload = {
        "seed": seed,
        "ticks": ticks,
        "legacy": legacy,
        "comparison": compare_integrated_legacy(integrated_result, legacy),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "exported": True,
        "path": str(output_path),
        "action_overlap_ratio": payload["comparison"]["action_overlap_ratio"],
        "hash_match": payload["comparison"]["hash_match"],
    }
