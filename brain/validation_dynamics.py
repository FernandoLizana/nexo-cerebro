"""
Validación científica E1–E8 — item 98.

Manifest 10k multi-seed + smoke compacto para CI (no corre 10k×20 en pytest).
Nunca escribe choice_key.
"""

from __future__ import annotations

import importlib.util
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .experiment_flags import apply_condition


@dataclass(frozen=True)
class BatteryExperiment:
    experiment_id: str
    title: str
    runner: str
    profile: str
    default_seeds: int
    default_steps: int
    notes: str = ""


BATTERY_E1_E8: tuple[BatteryExperiment, ...] = (
    BatteryExperiment("E1", "Ablaciones PFC/bind/hippo", "experiments.run_batch", "10k", 20, 200),
    BatteryExperiment("E2", "Invarianza LLM headless", "experiments.run_batch", "10k", 20, 100),
    BatteryExperiment("E3", "Sueño vs recall", "experiments.run_sleep", "10k", 20, 0),
    BatteryExperiment("E4", "Sueño selectivo", "experiments.run_e4_sleep_selective", "compact", 20, 0),
    BatteryExperiment("E5", "Grounding chat", "experiments.run_e5_grounding", "compact", 20, 0),
    BatteryExperiment("E6", "Bench tick GPU", "experiments.bench_tick_gpu", "10k", 5, 0),
    BatteryExperiment("E7", "Multimodal gain", "experiments.run_e7_multimodal", "compact", 20, 0),
    BatteryExperiment("E8", "Arena affordances L2", "experiments.run_arena_level24", "compact", 10, 0),
)


@dataclass
class ValidationDynamicsStack:
    last_smoke: dict[str, Any] = field(default_factory=dict)
    last_manifest: dict[str, Any] = field(default_factory=dict)

    def battery_manifest(self, *, profile: str = "10k", seeds: int = 20) -> dict[str, Any]:
        rows = []
        for exp in BATTERY_E1_E8:
            use_profile = profile if exp.experiment_id in ("E1", "E2", "E3", "E6") else exp.profile
            rows.append(
                {
                    "id": exp.experiment_id,
                    "title": exp.title,
                    "runner": exp.runner,
                    "profile": use_profile,
                    "seeds": seeds if exp.default_seeds >= 20 else exp.default_seeds,
                    "steps": exp.default_steps,
                    "command_hint": self._command_hint(exp, use_profile, seeds),
                }
            )
        out = {
            "profile_primary": profile,
            "seeds_recommended": seeds,
            "experiments": rows,
            "agency_note": "Batch runners are headless; PFC selects actions during sim",
        }
        self.last_manifest = out
        return out

    @staticmethod
    def _command_hint(exp: BatteryExperiment, profile: str, seeds: int) -> str:
        if exp.experiment_id == "E1":
            return f"python -m {exp.runner} --condition full --seeds {seeds} --steps {exp.default_steps} --profile {profile}"
        if exp.experiment_id == "E2":
            return f"python -m {exp.runner} --e2 --seeds {seeds} --steps {exp.default_steps} --profile {profile}"
        if exp.experiment_id == "E3":
            return f"python -m {exp.runner} --seeds {seeds} --profile {profile}"
        return f"python -m {exp.runner}  # see module --help; profile={profile}"

    def run_smoke(
        self,
        *,
        seeds: int = 2,
        steps: int = 8,
        condition: str = "full",
    ) -> dict[str, Any]:
        """Smoke E1-like compact — valida pipeline sin 10k×20."""
        from experiments.metrics import extract_tick_metrics
        from experiments.run_batch import run_simulation

        from .mind import InfantApeBrain
        from .profile import COMPACT_PROFILE

        summaries: list[dict[str, Any]] = []
        for seed in range(seeds):
            sd = Path(tempfile.mkdtemp(prefix=f"nexo_smoke_{seed}_"))
            try:
                np.random.seed(seed)
                brain = InfantApeBrain(
                    profile=COMPACT_PROFILE,
                    state_dir=sd,
                    headless=True,
                    auto_save=False,
                    experiment_flags=apply_condition(condition),
                )
                brain.world._rng = np.random.default_rng(seed)  # noqa: SLF001
                for t in range(steps):
                    out = brain.world_tick(steps=1)
                    row = extract_tick_metrics(out, tick=t, seed=seed, condition=condition)
                    if t == steps - 1:
                        summaries.append(
                            {
                                "seed": seed,
                                "mean_agency": row.agency,
                                "choice_key": row.choice_key,
                                "remembered": row.remembered,
                            }
                        )
            finally:
                shutil.rmtree(sd, ignore_errors=True)

        runner_ok = importlib.util.find_spec("experiments.run_batch") is not None
        out = {
            "ok": bool(summaries) and runner_ok,
            "seeds": seeds,
            "steps": steps,
            "condition": condition,
            "summaries": summaries,
            "battery_size": len(BATTERY_E1_E8),
            "manifest_preview": self.battery_manifest(profile="10k", seeds=20),
        }
        self.last_smoke = {k: v for k, v in out.items() if k != "manifest_preview"}
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "battery": [e.experiment_id for e in BATTERY_E1_E8],
            "last_smoke": self.last_smoke,
            "last_manifest_keys": list(self.last_manifest.keys()),
            "agency_note": "Validation observes metrics only; deliberation selects actions",
        }
