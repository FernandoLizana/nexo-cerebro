# FINAL_VALIDATION_REPORT

- timestamp_utc: 2026-07-22T23:03:45Z
- git_commit: `NO_GIT_REPOSITORY`

## Conclusion

READY FOR MANUSCRIPT FINALIZATION

## What was run

| Block | Profile | Seeds | Notes |
|-------|---------|-------|-------|
| A Baselines | compact | 20 | 100 ticks; study wrappers; under `raw_results/n20_compact/`; elapsed≈2162.48s |
| B Agency-break | compact | 20 | control vs full; elapsed≈857.27s |
| C Env shift | compact | 20 | transfer + discrimination Arena |
| D Historical E1-E3 | 10k | 5 | copied; not re-run |
| D Smoke | compact | 2 | short ticks (prior) |
| E Optional 10k smoke | 10k | 2×2 | optional; see SMOKE_NOTE |
| E Motor audit | n/a | n/a | static + pytest |

## Deferred (explicit)

- Full plan 6×20×long @10k baselines
- E1–E3 multi-seed **10k × 20** replication (NOT RUN — do not claim peer-review ready on this alone)
- Formal survival_time until death/termination; public ecological benchmark

## Issues / gaps

- 10k×20 E1–E3 replication NOT RUN (compute policy) — deferred
- External public benchmark EVIDENCE MISSING
- Formal survival_time (death/termination) MISSING; critical_state_tick_* is study proxy only

## Honesty

- Do **not** claim READY FOR PEER REVIEW while 10k×20 is missing.
- Compact n=20 A/B/C is the primary comparison for manuscript drafting; historical 10k n=5 remains separate.
- Legacy n=10 under `raw_results/baselines_A/` etc. preserved; primary pack uses n20_compact.

## Zip

- `NEXO_ADAPTIVE_BEHAVIOR_FINAL_PACK.zip` at repo root (mirrored under publication_finalization/)
