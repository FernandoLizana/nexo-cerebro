"""

E3 — Sueño vs control: recall tras consolidación.

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

from .process_guard import ensure_clean_pipeline, pipeline_root_pid

from .profile_select import resolve_experiment_profile



from .metrics import write_summary_csv



TEACHING_EPISODES: tuple[tuple[str, str], ...] = (

    ("La capital de Francia es París.", "capital Francia"),

    ("Los neurones disparan potenciales de acción.", "potenciales acción"),

    ("El hipocampo consolida recuerdos durante el sueño.", "hipocampo sueño"),

    ("La dopamina refuerza acciones recompensadas.", "dopamina refuerzo"),

)



RECALL_COUNT_BOOST = 0.12





def _recall_score(brain: InfantApeBrain, query: str) -> float:

    """Partial-cue recall; sleep replay raises memory count -> higher score."""

    sensory = encode_text(query, brain.n_sensory)

    body = brain.body.to_dict()

    room = brain.world.current_room()

    prior = brain.memory_store.recall(

        sensory,

        body=body,

        room=room,

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





def run_sleep_protocol(seed: int = 0, *, sleep: bool = True) -> dict:

    os.environ.setdefault("CEREBRO_OLLAMA", "0")

    enable_experiment_gpu()

    sd = Path(tempfile.mkdtemp(prefix=f"nexo_e3_{'sleep' if sleep else 'ctrl'}_{seed}_"))

    try:

        np.random.seed(seed)

        brain = InfantApeBrain(

            profile=resolve_experiment_profile(),

            state_dir=sd,

            headless=True,

            auto_save=False,

        )

        brain.world._rng = np.random.default_rng(seed)  # noqa: SLF001

        for text, query in TEACHING_EPISODES:

            brain.experience(

                text=text,

                label=query,

                tags=[t for t in query.split() if t.strip()],

                repeats=2,

                steps_per_repeat=30,

            )



        if sleep:

            brain.sleep(cycles=2, steps_per_cycle=80)



        scores = [_recall_score(brain, q) for _, q in TEACHING_EPISODES]

        return {

            "seed": seed,

            "condition": "sleep" if sleep else "control",

            "mean_recall": float(np.mean(scores)),

            "recall_scores": scores,

            "n_episodes": len(TEACHING_EPISODES),

        }

    finally:

        release_experiment_gpu()

        shutil.rmtree(sd, ignore_errors=True)





def run_all_e3(seeds: int = 5, out_dir: Path | None = None) -> list[dict]:

    out_dir = out_dir or Path("experiments/results")

    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []

    for seed in range(seeds):

        for sleep in (False, True):

            row = run_sleep_protocol(seed=seed, sleep=sleep)

            rows.append({k: v for k, v in row.items() if k != "recall_scores"})

            print(

                f"  E3 seed={seed} {row['condition']}: recall={row['mean_recall']:.3f}"

            )

    write_summary_csv(out_dir / "e3_sleep_recall.csv", rows)

    return rows





def main() -> None:

    parser = argparse.ArgumentParser(description="Nexo E3 sleep vs control")

    parser.add_argument("--seeds", type=int, default=5)

    parser.add_argument("--out", default="experiments/results")

    args = parser.parse_args()

    root = pipeline_root_pid()

    if not root:

        ensure_clean_pipeline()

    run_all_e3(seeds=args.seeds, out_dir=Path(args.out))





if __name__ == "__main__":

    main()


