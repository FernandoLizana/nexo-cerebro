# Publication Evidence Package — Adaptive Behavior (NEXO / cerebro)

**Purpose.** Supporting materials for `docs/planes/ARTEFACTO_PUBLICACION_ADAPTIVE_BEHAVIOR_NEXO.md`.  
**Rule.** Primary evidence = code, tests, CSVs/JSON under `experiments/results/`. Secondary = `docs/paper/*`. Do not treat generative drafts as experimental results.

## Contents

| Path | Role |
|------|------|
| `evidence_inventory.csv` | Machine-readable claim → path → status map |
| `missing_experiments.md` | Experiments still required for Adaptive Behavior |
| `reproduction_commands.md` | Exact CLI commands (read-only guidance; do not overwrite results) |
| `test_results/` | Optional quick unit-test logs (new only) |
| `figures/` | Placeholder for regenerated figures (do not invent data) |
| `tables/` | Optional derived tables |
| `logs/` | Optional run logs |

## Naming collision (critical)

| Label | Meaning in this project |
|-------|-------------------------|
| **CLEI E4** | Selective sleep (`experiments/run_e4_sleep_selective.py` → `e4_sleep_selective.csv`) |
| **Level 2 Arena / E8** | Causal affordance arenas (`experiments/run_arena_*.py`, results under `experiments/results/arena_*`) |

Do not cite “E4” without specifying which protocol.

## Neural-scale honesty (verified counts)

Computed via `brain.profile.profile_neuron_count`:

| Profile | Active LIF (approx.) |
|---------|----------------------|
| `COMPACT_PROFILE` | **624** |
| `VIRTUAL_LARGE_PROFILE` | **1,522** |
| `SCALE_10K_PROFILE` | **10,290** |
| `SCALE_50K_PROFILE` | **50,010** |

Virtual assemblies on disk and connectome scaffold logical nodes are **not** active LIF neurons.

## Agency core finding

**Sole writer of `choice_key`:** `PrefrontalDeliberation.run` in `brain/deliberation.py` (assigns `DeliberationResult.choice_key = winner.key`). Other modules may bias Go/drives/sensory/heading; they must not assign `choice_key` (documented in module headers; covered by unit tests).

## Primary result files (do not overwrite)

- E1: `experiments/results/e1_*_summary.csv`, `e1_*_s*.jsonl`
- E2: `experiments/results/e2_llm_invariance.csv`, `e2_llm_{on,off}_s*.jsonl`
- E3: `experiments/results/e3_sleep_recall.csv`
- E4: `experiments/results/e4_sleep_selective.csv`
- E5: `experiments/results/e5_grounding.csv`
- E7: `experiments/results/e7_multimodal.csv`
- Arena/E8: `experiments/results/arena_*.json`, `arena_*.csv`
- Bench: `experiments/results/bench_tick_gpu.csv`

Figures: `experiments/plot_figures.py` targets `experiments/figures/fig1–fig9`. **As of this audit, PNG files were not present in the workspace**; regenerate into `publication_evidence/figures/` if needed without overwriting any existing published assets.

## Author (only)

Fernando Andrés Lizana Núñez, Digital Rider SpA, Chile.
