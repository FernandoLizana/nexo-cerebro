# EXPERIMENTAL_PROTOCOL

| Field | Value |
|-------|-------|
| Package | NEXO Adaptive Behavior finalization |
| Date | 2026-07-22 |
| Profile (new runs) | `compact` (~624 active LIF) |
| Profile (historical E1–E3) | `neuro-10k` / SCALE_10K (10,290 LIF) |
| Seeds (A/B/C) | 0..9 (n=10) |
| Steps (A/B) | 100 ticks |
| Ollama | `CEREBRO_OLLAMA=0` |
| Process guard | `CEREBRO_SKIP_PROCESS_GUARD=1` for publication wrappers |
| Output root | `publication_finalization/` only |

## Phase A — Baselines (same protocol)

| Condition | Implementation | Notes |
|-----------|----------------|-------|
| `full` | `AblationFlags()` via `apply_condition("full")` | Reference |
| `reactive` | Study wrapper: after deliberation, set schema of argmax drive | Control baseline |
| `nohippo` | `disable_hippocampus=True` | Flag ablation |
| `no_homeostasis` | Freeze body vars + flat drives (wrapper) | Approximation — document as such |
| `nopfc` | `force_limbic_winner=True` | Flag ablation |
| `td_direct` | `enable_td_reward=True` + wrapper selects max TD value action | **Agency-break learner**; not default |

Metrics logged: agency, spike_aligned, remembered_rate, drive_coherent, homeostatic_abs_dev, agency_override_rate.  
`survival_time`: **MISSING** (not formalized).

## Phase B — Agency-break

| Condition | Implementation |
|-----------|----------------|
| `full` | Default |
| `agency_break` | Force eat/drink/wander from body hunger/thirst thresholds after deliberation |

Documented as **experimental control**, not an architecture improvement.

## Phase C — Environmental shift

Wrappers around existing Arena:

- `experiments.arena.task_transfer_fountain.run_transfer_fountain_arm`
- `experiments.arena.task_discrimination.run_discrimination_good_vs_dry`

Affordances on vs off; compact profile; n=10 seeds.

## Phase D — E1–E3

1. Copy existing CSVs from `experiments/results/` → `raw_results/historical/` (n=5, 10k) — **do not overwrite originals**.
2. Optional compact smoke: 2 seeds × short ticks for `full`/`nopfc`/`nohippo`.
3. Multi-seed 10k replication: **NOT RUN / deferred**.

## Phase E — Motor audit

Static assignment scan + targeted pytest (agency-preserving bias modules).

## Reproduce

See `REPRODUCTION_README.md`, `reproduce_all.ps1`, `reproduce_all.sh`.
