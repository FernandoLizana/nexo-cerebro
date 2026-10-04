# P4 — Regression report

**Date:** 2026-08-19 · **Verdict:** PASS — no unexplained regressions

## Quality gates (P4 prompt §137–147)

| Gate | Requirement | Result |
|------|-------------|--------|
| A — P3 preserved | Hybrid, limited perception, selector secrecy, attention | PASS |
| B — Goal representation | Declarative, serializable, step-free, auditable | PASS |
| C — Task context | Agent data only, no oracle/selectors/next step | PASS |
| D — Progress | Evidence-based, partial, non-monotonic | PASS |
| E — Autonomy | Goal yes, steps no, dynamic actions | PASS |
| F — Recovery | Wrong action → continue without script | PASS |
| G — Goal relevance | Influences deliberation, perception preserved | PASS |
| H — Policy | Goals cannot bypass security | PASS |
| I — Causality | goal.progress + action.selected traceable | PASS |
| J — Regression | No silent legacy breaks | PASS |
| K — No overclaim | Heuristic NL, not human reasoning | PASS |

## Test matrix

| Suite | Count | Result |
|-------|-------|--------|
| P4 goals | 22 | PASS |
| P3 perception | 20 | PASS |
| P2 browser | 11 | PASS |
| P1 contract | 26+ | PASS |
| P0 import | 1 | PASS |

## v90 golden

| Config | seed | ticks | Hash match |
|--------|------|-------|------------|
| `integrated_v90.yaml` | 42 | 12 | yes |

`77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c`

## Core changes scope

Minimal diffs in `nexo/prefrontal/deliberation.py` and `nexo/core/process_executive.py` — optional `goal_relevance` only. Legacy RoomWorld paths unchanged unless `bind_task` used.

## Pre-existing failures

`test_grounding` (P0) — not introduced by P4; do not “fix” unless intentional.
