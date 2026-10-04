# EVIDENCE_GAP_FILL — n=20 compact campaign

| Field | Value |
|-------|-------|
| Date | 2026-07-22 |
| Goal | Close PARTIALLY READY gaps from n=10 A/B/C without inventing results or touching NEXO core |
| Output root | `publication_finalization/raw_results/n20_compact/` (legacy n=10 paths **preserved**) |

## Protocol (comparability)

| Item | Choice | Rationale |
|------|--------|-----------|
| Profile | `compact` (~624 LIF) | Same as prior A/B/C; within compute policy |
| Seeds | **20** (0..19) | Requested fill; replaces underpowered n=10 as **primary** compact table |
| Ticks (A/B) | **100** | Match prior compact campaign for head-to-head comparability |
| Env shift (C) | Arena transfer + discrimination, 20 seeds × aff on/off | Same wrappers as n=10 |
| Historical E1–E3 | Not re-run | Still n=5 @10k under `raw_results/historical/` |
| 10k×20 replication | **Deferred** | Explicit; blocks READY FOR PEER REVIEW |

## Metrics from tick logs (honest)

| Metric | Status | Definition |
|--------|--------|------------|
| mean_agency, coherence, remembered, homeostatic_abs_dev | Logged | Unchanged |
| `action_entropy_bits` | **NEW from logs** | Shannon entropy (bits) of `choice_key` over ticks |
| `critical_state_tick_count` / `_rate` | **NEW study proxy** | Ticks with hunger≥0.85 OR thirst≥0.85 OR fatigue≥0.90 |
| `survival_time` | **MISSING** | Episode death/termination not formalized in core — field remains `MISSING_not_formalized` |

Critical-state counts are **not** survival_time and must not be relabeled as such.

## Runner

```text
.venv\Scripts\python.exe publication_finalization\scripts\run_publication_experiments.py ^
  --phase all --seeds 20 --steps 100 --profile compact --out-root n20_compact
```

Optional cheap 10k smoke (after A/B/C if time allows):

```text
.venv\Scripts\python.exe publication_finalization\scripts\run_publication_experiments.py ^
  --phase E10k_smoke --seeds 2 --steps 40 --profile 10k --out-root n20_compact
```

## Stats / pack refresh

1. `scripts/build_stats.py` — prefers `n20_compact`; writes `*_n20.csv` mirrors
2. `figure_scripts/plot_publication_figures.py` — regenerates A/B/C figures from n20
3. `scripts/pack_final.py` — zip + `FINAL_VALIDATION_REPORT.md`

## Expected wall-clock (this laptop)

Prior n=10: A ≈ 1074 s, B ≈ 479 s. Scale ×2 → A ≈ **0.6 h**, B ≈ **0.3 h**, C Arena ≈ **0.5–2 h** depending on task length. Total order **1.5–3 h**.

## Measured wall-clock (n20_compact, 2026-07-22)

| Block | Seeds | Elapsed |
|-------|-------|---------|
| A Baselines | 20 × 6 cond × 100 ticks | **2162.48 s** (~36.0 min) |
| B Agency-break | 20 × 2 × 100 | **857.27 s** (~14.3 min) |
| C Env shift | 20 × transfer/discrim × aff | **~580.6 s** (~9.7 min) |
| Optional 10k smoke | 2 × full/nopfc × 40 ticks | **60.48 s** |
| **A+B+C total** | | **~3600 s (~1.0 h)** |

Source: `raw_results/n20_compact/CAMPAIGN_RUNTIME.json` + A/B `run_meta.json`.

## Verdict policy

- If A/B/C n=20 complete + honest stats: **READY FOR MANUSCRIPT FINALIZATION** with deferred 10k×20 / survival / public benchmark.
- Do **not** claim READY FOR PEER REVIEW while 10k×20 missing.
- If n=20 fails: keep **PARTIALLY READY — MISSING EXPERIMENTS**.
