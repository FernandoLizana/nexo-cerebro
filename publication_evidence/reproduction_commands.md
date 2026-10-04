# Reproduction Commands — NEXO / cerebro

**Warning.** Do **not** overwrite existing files under `experiments/results/` if they are treated as publication assets. Redirect new runs to `publication_evidence/logs/` or a dated subfolder.

**Environment (verified dependencies file):** `requirements.txt`  
`flask>=3.0,<4`, `numpy>=1.26,<3`, `scipy>=1.11,<2`, `pillow>=10.0,<12`, `pypdf>=4.0,<7`, `matplotlib>=3.8,<4`  
Optional GPU: CuPy (not pinned in `requirements.txt`) — [DETAIL REQUIRED] for exact CUDA/CuPy versions used in original E1 GPU rows.

```bash
cd .
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
pip install pytest  # for unit tests
```

## Profile selection

```bash
# Paper E1–E3 profile
set CEREBRO_EXPERIMENT_PROFILE=10k
# or CLI --profile 10k

# Smoke / E4 / E5 / E7 / Arena
set CEREBRO_EXPERIMENT_PROFILE=compact
```

Neuron counts (do not round incorrectly in manuscript):

```bash
python -c "from brain.profile import COMPACT_PROFILE, VIRTUAL_LARGE_PROFILE, SCALE_10K_PROFILE, profile_neuron_count as n; print(n(COMPACT_PROFILE), n(VIRTUAL_LARGE_PROFILE), n(SCALE_10K_PROFILE))"
# Expected: 624 1522 10290
```

## Unit tests (agency-related; safe)

```bash
python -m pytest tests/test_grounding.py tests/test_affordance_map.py tests/test_td_reward.py tests/test_intention_circuit.py tests/test_arena_thirst.py -q
```

Audit log example: `publication_evidence/test_results/agency_unit_tests.txt` (23 passed, 2026-07-22).

## E1–E3 (heavy — hours possible on 10k)

```bash
# Full published pipeline (will write under experiments/results/)
python -m experiments.run_all --profile 10k --seeds 5 --steps 200 --workers 2

# Individual
python -m experiments.run_e1_parallel --profile 10k --seeds 5 --workers 2 --parallel-seeds 2
python -m experiments.run_batch --e2 --seeds 5 --steps 100 --profile 10k
python -m experiments.run_sleep --seeds 5 --profile 10k
```

## E4 / E5 / E7 (compact; CLEI naming)

```bash
set CEREBRO_SKIP_PROCESS_GUARD=1
python -m experiments.run_e4_sleep_selective --seeds 5 --profile compact
python -m experiments.run_e5_grounding --seeds 5 --profile compact
python -m experiments.run_e7_multimodal --seeds 5 --profile compact
```

## Arena / Level 2 (= E8 in CLEI numbering)

```bash
python -m experiments.run_arena_thirst --seeds 3 --profile compact
python -m experiments.run_arena_extra
python -m experiments.run_arena_level24
python -m experiments.run_arena_level25
```

## Figures (do not invent data)

```bash
# Default writes to experiments/figures/ — prefer copying to publication_evidence/figures/
python -m experiments.plot_figures --in experiments/results
```

## Bench

```bash
python -m experiments.bench_tick_gpu --profiles compact,10k --ticks 5
```

## Determinism notes

- E1 `full` summary rows are **identical across seeds 0–4** in `e1_full_summary.csv` (low stochasticity / determinism) — report honestly.
- E2 CSV: `trajectories_identical=True` for seeds 0–4 (`e2_llm_invariance.csv`).
- E5/E7 compact rows often identical across seeds — treat as low-variance smoke, not population inference.
