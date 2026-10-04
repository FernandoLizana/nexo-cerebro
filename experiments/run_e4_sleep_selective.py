"""
E4 — Sueño selectivo vs uniforme vs control: recall emocional vs neutro.

Hipótesis: under selective replay, mean recall of high-|valence| episodes
improves more than neutral ones, relative to uniform sleep / no sleep.

El sueño no elige acciones (agency intacta).
"""

from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np

from brain.encode import encode_text
from brain.mind import InfantApeBrain

from .gpu_env import enable_experiment_gpu, release_experiment_gpu
from .metrics import write_summary_csv
from .process_guard import ensure_clean_pipeline, pipeline_root_pid
from .profile_select import resolve_experiment_profile

# (text, query, valence, kind)
TEACHING: tuple[tuple[str, str, float, str], ...] = (
    ("Un incendio destruyó la casa y sentí terror absoluto.", "incendio terror", -0.88, "emotional"),
    ("El abrazo de Nira me llenó de alegría profunda.", "abrazo alegría", 0.82, "emotional"),
    ("La capital de Francia es París.", "capital Francia", 0.05, "neutral"),
    ("Los neurones disparan potenciales de acción.", "potenciales acción", 0.05, "neutral"),
)

RECALL_COUNT_BOOST = 0.12


def _recall_score(brain: InfantApeBrain, query: str) -> float:
    sensory = encode_text(query, brain.n_sensory)
    prior = brain.memory_store.recall(
        sensory,
        body=brain.body.to_dict(),
        room=brain.world.current_room(),
        motor=[],
        semantic_text=query,
        threshold=0.0,
    )
    if prior is None:
        hits = brain.memory_store.search_by_tags(
            [t for t in query.split() if t.strip()],
            k=1,
        )
        if hits:
            prior = hits[0]
            base = 0.42
        else:
            return 0.0
    else:
        base = float(prior.get("similarity", 0.0))
    count = int(prior.get("count", 1))
    boost = min(0.36, RECALL_COUNT_BOOST * max(0, count - 1))
    return float(np.clip(base + boost, 0.0, 1.0))


def _teach(brain: InfantApeBrain) -> None:
    for text, query, valence, kind in TEACHING:
        tags = [t for t in query.split() if t.strip()] + [kind]
        if kind == "emotional":
            tags.append("emotional")
        brain.experience(
            text=text,
            label=query,
            tags=tags,
            repeats=2,
            steps_per_repeat=24,
        )
        brain.memory_store.set_memory_affect(
            query=query,
            valence=valence,
            arousal=0.75 if kind == "emotional" else 0.25,
            extra_tags=["emotional"] if kind == "emotional" else ["neutral"],
        )


def run_e4_protocol(seed: int, condition: str) -> dict:
    """
    condition: control | uniform | selective
    """
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    enable_experiment_gpu()
    sd = Path(tempfile.mkdtemp(prefix=f"nexo_e4_{condition}_{seed}_"))
    try:
        np.random.seed(seed)
        brain = InfantApeBrain(
            profile=resolve_experiment_profile(),
            state_dir=sd,
            headless=True,
            auto_save=False,
        )
        brain.world._rng = np.random.default_rng(seed)  # noqa: SLF001
        _teach(brain)

        if condition == "uniform":
            brain.sleep(cycles=2, steps_per_cycle=60, replay_mode="uniform")
        elif condition == "selective":
            brain.sleep(cycles=2, steps_per_cycle=60, replay_mode="selective")
        elif condition != "control":
            raise ValueError(f"unknown condition {condition!r}")

        emo_scores = []
        neu_scores = []
        for _, query, _, kind in TEACHING:
            sc = _recall_score(brain, query)
            if kind == "emotional":
                emo_scores.append(sc)
            else:
                neu_scores.append(sc)

        return {
            "seed": seed,
            "condition": condition,
            "mean_recall_emotional": float(np.mean(emo_scores)),
            "mean_recall_neutral": float(np.mean(neu_scores)),
            "mean_recall_all": float(np.mean(emo_scores + neu_scores)),
            "emotion_advantage": float(np.mean(emo_scores) - np.mean(neu_scores)),
            "n_emotional": len(emo_scores),
            "n_neutral": len(neu_scores),
        }
    finally:
        release_experiment_gpu()
        shutil.rmtree(sd, ignore_errors=True)


def run_all_e4(seeds: int = 5, out_dir: Path | None = None) -> list[dict]:
    out_dir = out_dir or Path("experiments/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for seed in range(seeds):
        for cond in ("control", "uniform", "selective"):
            row = run_e4_protocol(seed=seed, condition=cond)
            rows.append(row)
            print(
                f"  E4 seed={seed} {cond}: "
                f"emo={row['mean_recall_emotional']:.3f} "
                f"neu={row['mean_recall_neutral']:.3f} "
                f"adv={row['emotion_advantage']:+.3f}",
                flush=True,
            )
    write_summary_csv(out_dir / "e4_sleep_selective.csv", rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexo E4 selective sleep recall")
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--out", default="experiments/results")
    parser.add_argument("--profile", default=None, help="compact | 10k | large")
    args = parser.parse_args()
    if args.profile:
        os.environ["CEREBRO_EXPERIMENT_PROFILE"] = args.profile
    root = pipeline_root_pid()
    if not root:
        ensure_clean_pipeline()
    run_all_e4(seeds=args.seeds, out_dir=Path(args.out))


if __name__ == "__main__":
    main()
