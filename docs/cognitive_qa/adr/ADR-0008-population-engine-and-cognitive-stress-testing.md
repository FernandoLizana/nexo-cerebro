# ADR-0008 — Population Engine and Cognitive Stress Testing

## Status

Accepted — P7

## Context

P6 analyzes individual cognitive QA runs. P7 must scale to populations (tasks × personas × seeds × conditions) while preserving individual traces, certificates, and P6 metric definitions.

## Decision

1. Add `nexo_qa/population/` with versioned `PopulationSpec`, deterministic planning, resource-bounded runner, and aggregator.
2. P6 remains the **single-run source of truth** — runner calls `capture_run_trace` + `analyze_raw_trace`; no duplicated NCFS/EHFP/CRS.
3. Seeds are hash-derived and reordering-invariant; parallelism does not affect plan identity.
4. Infrastructure failures (`FAILED_INFRASTRUCTURE`) are separable from task failures; only infra gets automatic retry.
5. Reports include explicit simulation disclaimers — not human population claims.
6. CI uses `trace_fixture` backend; browser populations remain opt-in.

## Consequences

- P8 can add condition sets (e.g. interruptions) without new aggregation logic.
- Population artifacts live under `artifacts/p7/populations/<id>/`.
- v90 NEXO core trajectory unchanged; P7 is additive under `nexo_qa/`.
