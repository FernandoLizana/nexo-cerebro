# STATISTICAL_REPORT

- Generated: 2026-07-22T23:01:41Z
- git_commit: `NO_GIT_REPOSITORY`
- Primary A/B/C campaign: `n20_compact`
- Seed-level rows: 290
- Master groups: 25
- Pairwise rows: 16
- Compact A full-condition seeds: 20

## Policy

- Only real CSVs under `publication_finalization/raw_results/` (+ copied historical).
- Bootstrap 95% CI for means when **n≥3** (5000 resamples, seed 0).
- Mann–Whitney normal approximation when n≥3 per arm.
- Compact A/B/C primary: **n=20** seeds × 100 ticks (see `EVIDENCE_GAP_FILL.md`). Historical E1–E3 remain **n=5 @10k**.
- Zero across-seed variance (common in E1 full) makes inferential tests degenerate — report descriptives explicitly.
- Do **not** mix compact A/B/C with historical 10k E1–E3 in one unlabeled inference.
- `action_entropy_bits` / `critical_state_tick_*` are study-derived from tick logs; `survival_time` remains **MISSING**.

## Blocks present

- `A_baselines`: 120 seed-level rows
- `B_agency_break`: 40 seed-level rows
- `C_env_shift`: 80 seed-level rows
- `D_historical_E1_10k`: 25 seed-level rows
- `D_historical_E2_10k`: 5 seed-level rows
- `D_historical_E3_10k`: 10 seed-level rows
- `D_smoke_compact`: 6 seed-level rows
- `E_10k_smoke`: 4 seed-level rows

## Files

- `SEED_LEVEL_RESULTS.csv` (+ `*_n20.csv` when campaign is n20_compact)
- `FINAL_RESULTS_MASTER.csv`
- `PAIRWISE_COMPARISONS.csv`

## Deferred / missing

- Full 10k × 20-seed replication of E1–E3: **NOT RUN / deferred**
- Formal survival_time (episode until death/termination): **MISSING** (not formalized in core)
- External public benchmark: **MISSING**
- Multiple-comparison Holm across all DVs: not applied globally (exploratory pairwise only)
