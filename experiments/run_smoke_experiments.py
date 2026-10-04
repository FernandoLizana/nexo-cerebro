#!/usr/bin/env python3
"""Smoke experiments con ExperimentResult real."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from nexo.environment import git_commit, git_dirty
from nexo.experiment_conditions import get_condition
from nexo.result_schema import ExperimentResult, trajectory_hash

SMOKE_RUNS = (
    ("baseline_legacy", 42),
    ("roadmap100_full_v1", 42),
    ("roadmap100_full_v1", 99),
    ("roadmap100_no_binding_v1", 42),
    ("roadmap100_no_pfc_v1", 42),
)
STEPS = 8


def _run_one(condition_id: str, seed: int, out_dir: Path) -> Path:
    from brain.mind import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    cond = get_condition(condition_id)
    er = ExperimentResult.start(
        experiment="smoke",
        condition=cond.condition_id,
        seed=seed,
        config_hash=cond.config_hash(),
        flags=cond.flags_dict(),
        parameters={"steps": STEPS},
        commit=git_commit(),
        dirty=bool(git_dirty()),
    )
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        headless=True,
        auto_save=False,
        seed=seed,
        condition_id=cond.condition_id,
        experiment_flags=cond.flags,
    )
    traj = []
    metrics_acc = {"legacy_agency_sum": 0.0, "ticks": 0}
    for _ in range(STEPS):
        out = brain.world_tick(steps=1)
        delib = out.get("deliberation") or {}
        traj.append({"choice_key": delib.get("choice_key"), "agency": delib.get("agency")})
        metrics_acc["legacy_agency_sum"] += float(delib.get("agency", 0))
        metrics_acc["ticks"] += 1
    er.metrics = {
        **metrics_acc,
        "mean_legacy_agency": metrics_acc["legacy_agency_sum"] / max(metrics_acc["ticks"], 1),
    }
    er.trajectory_hash = trajectory_hash(traj)
    er.finish()
    out_path = out_dir / f"{condition_id}_seed_{seed}.json"
    out_path.write_text(er.to_json(), encoding="utf-8")
    return out_path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    out_dir = root / "results" / "smoke"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for cond, seed in SMOKE_RUNS:
        written.append(str(_run_one(cond, seed, out_dir)))
    print(json.dumps({"written": written, "count": len(written)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
