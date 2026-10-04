# CURRENT_EVIDENCE_AUDIT — NEXO Adaptive Behavior

| Field | Value |
|-------|-------|
| Audit date | 2026-07-22 |
| Repo | `cerebro` (NEXO) |
| Rule | No invented results; mark gaps honestly |
| Git commit | **NO_GIT_REPOSITORY** (workspace has no `.git`) |

## Claim → evidence table

| Claim | Evidence File | Function/Class | Result File | Status | Limitation |
|-------|---------------|----------------|-------------|--------|------------|
| Sole writer of `choice_key` under audited paths is PFC deliberation | `brain/deliberation.py` | `PrefrontalDeliberation.run` → `choice_key=winner.key` | unit tests (`tests/test_grounding.py`, `test_affordance_map.py`, `test_td_reward.py`, `test_s7_scale_motor_multi.py`) | **VERIFIED** (code + tests) | Agency-break wrappers in this package deliberately violate for control; not default |
| HUD `agency_guard` is declarative (does not prove safety) | `brain/causal_hud.py` | `build_causal_hud` → `agency_guard` dict | `tests/test_demo_hud.py`, `tests/test_level23.py` | **VERIFIED** declarative | Not a formal proof / runtime enforcer |
| Affordance learning is Go-bias only (cap ±0.08) | `brain/affordance_map.py` | `AFFORDANCE_BIAS_MAX`, `biases_for` | Arena JSON under `experiments/results/`; tests | **VERIFIED** | Compact Arena N small |
| TD is Go-bias only by default (cap 0.10); never writes `choice_key` | `brain/td_reward.py` | `go_biases`, module docstring | `tests/test_td_reward.py` | **VERIFIED** default | Study `td_direct` wrapper **forces** choice for baseline contrast only |
| Grounding biases drives/sensory; does not write `choice_key` | `brain/grounding.py` | merge helpers | `e5_grounding.csv`; `tests/test_grounding.py` | **PARTIALLY VERIFIED** | Compact; locomotion deltas weak |
| LLM verbalization outside motor path (headless) | `brain/language_cortex.py` | LanguageCortex | `e2_llm_invariance.csv` | **VERIFIED** under headless protocol | May not invoke live Ollama in headless |
| LIF profiles: compact / virtual / 10k active counts | `brain/profile.py` | profile constructors + `profile_neuron_count` | `bench_tick_gpu.csv` (624 / 10290) | **VERIFIED** | Marketing “~500/~10k” approximate |
| Sleep / replay architecture | `brain/sleep_architecture.py` | `SleepArchitecture` | `e3_sleep_recall.csv`, `e4_sleep_selective.csv` | **PARTIALLY VERIFIED** | Custom recall metric; E4 mixed |
| Hippocampus ablation zeros `remembered_rate` | `experiment_flags.disable_hippocampus` | E1 runner | `e1_nohippo_summary.csv` | **VERIFIED** (n=5, 10k) | Strong determinism across seeds |
| PFC ablation zeros `agency` | `force_limbic_winner` | E1 | `e1_nopfc_summary.csv` | **VERIFIED** (n=5, 10k) | Internal metric ≠ free will |
| Binding ablation zeros `spike_aligned` | `bind_deliberation=False` | E1 | `e1_nobind_summary.csv` | **VERIFIED** (n=5, 10k) | |
| Embodied body / world loop | `brain/body.py`, `brain/world.py` | `BodyState`, `apply_motor` | demos ≠ experiments | **VERIFIED** code | 2D symbolic home |
| Comparative baselines (reactive, no-homeostasis, TD-direct, …) | — | — | prior: **EVIDENCE MISSING** | **NEW** under `raw_results/baselines_A/` (compact, n=10, 100 ticks) | Not 10k; short horizon; wrappers |
| Agency-break control | — | study patch `force_body_schema` | `raw_results/agency_break_B/` | **NEW** compact | Control, not improvement |
| Environmental shift / transfer | `experiments/arena/task_transfer_fountain.py`, `task_discrimination.py` | Arena runners | historical JSON + `raw_results/env_shift_C/` | **PARTIAL** → extended in package | Profile compact |
| External public benchmark | — | — | — | **EVIDENCE MISSING** | |
| Human brain / consciousness / free will / AGI | — | — | — | **NOT CLAIMED** | Flag names may contain “consciousness”; treat as module labels only |
| Flask / UI demos | `app.py` | — | — | **NOT scientific experiments** | Do not cite as results |

## Flag map (paper defaults)

From `brain/experiment_flags.py` `AblationFlags()` defaults: TD/grounding/affordances/selective sleep/limited WM/attention budget **OFF** for paper batch; demo may enable via env.

## Metric honesty

| Metric | Computable from tick logs? | Notes |
|--------|----------------------------|-------|
| mean_agency, spike_aligned, remembered_rate, drive_coherent | Yes | Custom internal |
| homeostatic_abs_dev | Yes (this package logs body) | Study-defined setpoints |
| survival_time | **MISSING** | Not formalized in core; do not invent |
| ecological fitness / public benchmark score | **MISSING** | |

## Profile mixing warning

- Historical E1–E3: **SCALE_10K_PROFILE** (10,290 LIF), n=5.
- New A/B/C and D-smoke: **COMPACT** (~624 LIF), n=10 (smoke n=2).
- Never merge into one unlabeled primary table.
