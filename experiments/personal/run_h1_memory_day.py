"""Corrida H1 — 24h simuladas con legacy_brain + memory unification."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE
from nexo.behavioral.causal_certificate import summarize_causal_certificates
from nexo.behavioral.memory_bridge import summarize_memory_bridge
from nexo.behavioral.memory_unification import summarize_memory_unification
from nexo.demo.day_in_the_life import build_day_timeline, day_in_the_life_ticks
from nexo.integrated_runtime import _repo_root, runtime_from_config


def main() -> int:
    root = _repo_root()
    out_dir = root / "results" / "personal" / "H1_memory"
    out_dir.mkdir(parents=True, exist_ok=True)

    seed = 42
    sd = Path(tempfile.mkdtemp(prefix="nexo_h1_"))
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        seed=seed,
    )
    rt = runtime_from_config(root / "configs/nexo/integrated_v80.yaml", legacy_brain=brain)
    rt.config.seed = seed
    n = day_in_the_life_ticks(simulated_hours=24.0, seconds_per_tick=rt.clock.seconds_per_tick)
    rt.config.ticks = n
    result = rt.run()

    payload = {
        "seed": seed,
        "ticks": n,
        "simulated_hours": round(rt.clock.simulation_seconds / 3600.0, 3),
        "memory_unification": summarize_memory_unification(rt),
        "memory_bridge": summarize_memory_bridge(rt),
        "causal_certificates": summarize_causal_certificates(rt),
        "timeline": build_day_timeline(rt),
        "runtime_summary": {
            "sleep_phase": result.get("sleep_phase"),
            "sleep_cycles": result.get("sleep_cycles"),
            "memory_consolidations": result.get("memory_consolidations"),
            "hippocampal_episodes": result.get("hippocampal_episodes"),
            "memory_replays": result.get("memory_replays"),
        },
    }
    out_path = out_dir / "h1_day_run_seed42.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"exported": True, "path": str(out_path), **payload["memory_unification"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
