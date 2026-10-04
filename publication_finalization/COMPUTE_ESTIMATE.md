# COMPUTE_ESTIMATE — NEXO Adaptive Behavior Finalization

| Field | Value |
|-------|-------|
| Date | 2026-07-22 |
| Machine | Intel Core 5 210H (8c/12t), 24 GB RAM, Windows 10/11 build 26200 |
| Python | 3.11.0 (`.venv`) |
| GPU (this session) | Not assumed available; prior E1 CSV used RTX 3050 6GB Laptop |
| Tick bench (repo `bench_tick_gpu.csv`) | compact ≈ **16.4 ms/tick**; 10k ≈ **23.7 ms/tick** (CPU fallback in that bench) |
| Construct overhead | ~2.0–2.6 s per brain (bench) |

## Full plan (as originally specified)

Assumptions for upper-bound estimate:

| Block | Spec | Tick cost (order) | Wall-clock (order) | Peak RAM | Disk |
|-------|------|-------------------|--------------------|----------|------|
| A Baselines | 6 conditions × 20 seeds × 500 ticks @ **10k** | 6×20×500×24 ms ≈ 1.4×10³ s ticks + ~120 constructs × 2.6 s | **~1.5–3 h** | ~0.2–0.5 GB RSS/process; higher with GPU | ~few hundred MB JSONL |
| B Agency-break | 2 conditions × 20 × 500 @ 10k | ~ half of A | **~0.5–1.5 h** | similar | tens of MB |
| C Env shift | transfer/discrim × 20 seeds × ~140 ticks × arms | smaller | **~0.5–2 h** | similar | tens of MB |
| D E1–E3 | 5+ conditions × 20 × 200 @ 10k (+ E2/E3) | E1 alone ≈ 5×20×200×24 ms ≈ 480 s + construct | **~2–6 h** (workers help) | similar | **large** JSONL (existing 5-seed set already ~1–2 MB/file) |
| E Motor audit | static + unit tests | n/a | **minutes** | low | small |

**Full-plan total (conservative):** **≈ 8–15+ hours** wall-clock on this laptop without aggressive parallelism; disk for new 10k×20 JSONL can exceed **several GB** if all ticks logged.

**Thresholds:** >8 h wall OR >10 GB new disk → **must use COMPACT primary plan** (policy).

## Decision: COMPACT primary comparison

| Decision | Detail |
|----------|--------|
| **Primary profile** | `COMPACT_PROFILE` (~**624** active LIF; marketing “~500”) |
| **Why** | Full 10k×20×long + E1–E3×20×10k exceeds 8 h and risks large JSONL growth; GPU may be unavailable |
| **Seeds (gap-fill)** | **20** for A/B/C under `raw_results/n20_compact/` (legacy n=10 retained, not overwritten) |
| **Ticks (A/B)** | **100** ticks/seed (match prior compact for comparability; short vs paper E1 200 @10k) |
| **E1–E3 (D)** | **Do not re-run** full 10k×20. Copy existing `experiments/results/` summaries + note n=5 historical. Optional smoke: 2 seeds compact / optional 10k 2×2 |
| **10k multi-seed replication** | **NOT RUN / deferred** |
| **Silent skips** | **None** — each reduction listed below |

## What will run vs deferred

| ID | Plan | Status in this package |
|----|------|------------------------|
| A Baselines | compact, **20** seeds, 100 ticks: `full`, `reactive`, `nohippo`, `no_homeostasis`, `nopfc`, `td_direct` | **RUN** under `raw_results/n20_compact/baselines_A/` |
| B Agency-break | compact, **20** seeds, 100 ticks: `full` vs `force_drive_choice` wrapper | **RUN** under `n20_compact/agency_break_B/` |
| C Env shift | transfer/discrim Arena; compact, **20** seeds | **RUN** under `n20_compact/env_shift_C/` |
| D E1–E3 | historical CSV/JSONL copy; optional 2-seed compact smoke | **HISTORICAL COPY** + optional smoke |
| E Motor audit | static inspection + targeted pytest | **RUN** (report only) |
| Optional 10k smoke | 2 seeds × full/nopfc, short ticks | **OPTIONAL** if time allows |
| Full 10k×20 baselines | — | **DEFERRED** (compute) |
| E1–E3 10k×20 | — | **DEFERRED / NOT RUN** |
| Formal survival_time | — | **MISSING**; proxies: action entropy + critical-state tick rate (see EVIDENCE_GAP_FILL.md) |

See also `EVIDENCE_GAP_FILL.md` for wall-clock of the n=20 campaign and metric definitions.

## Disk budget (expected new writes)

| Path | Expected |
|------|----------|
| `publication_finalization/raw_results/` | < 200 MB (compact summaries + sparse JSONL) |
| Zip package (sanitized) | target **≪ 10 GB**; exclude `.venv`, `.git`, secrets, huge jsonl dumps |

## Honesty note

Compact short-horizon runs are **comparable among themselves** under one protocol. They are **not** substitutes for historical 10k E1–E3 tables. Never mix profiles in one primary results table without labeling.
