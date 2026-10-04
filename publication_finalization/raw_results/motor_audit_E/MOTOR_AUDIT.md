# MOTOR_AUDIT — Static code inspection + smoke tests

| Field | Value |
|-------|-------|
| Date | 2026-07-22 |
| Scope | Who can write / bias motor `choice_key` and locomotion |
| Method | Static inspection of cited modules + targeted unit tests |
| Core behavior changed? | **No** (audit only; study wrappers live under `publication_finalization/scripts/`) |

## Executive finding

Under **default** `AblationFlags` and audited call paths, **`PrefrontalDeliberation.run` is the sole assignment of `DeliberationResult.choice_key`**. Learning modules (affordance, TD, grounding, counterfactual) apply **bounded Go / drive biases** and do not set `choice_key`. HUD `agency_guard` is **declarative telemetry**, not an enforcer.

Study-only wrappers in this package (`reactive`, `td_direct`, `agency_break`) **intentionally** overwrite `choice_key` after deliberation for experimental controls. They are **not** product defaults.

## Writer / bias map

| Module | Path | Can write `choice_key`? | Role | Evidence |
|--------|------|-------------------------|------|----------|
| Prefrontal deliberation | `brain/deliberation.py` | **YES** | Contest → `choice_key=winner.key` | Code L413 area; grep |
| Agent loop | `brain/agent_loop.py` | Passes through / logs | Executes after deliberation | Uses `delib.choice_key` |
| Affordance map | `brain/affordance_map.py` | **NO** | Go bias ≤ `AFFORDANCE_BIAS_MAX` (0.08) | Module + tests |
| TD reward | `brain/td_reward.py` | **NO** (default) | Go bias ≤ `TD_GO_BIAS_MAX` (0.10) | Docstring + `go_biases` |
| Grounding | `brain/grounding.py` | **NO** | Drive/sensory bias | Tests assert unchanged choice |
| Language / LLM | `brain/language_cortex.py` | **NO** (architected) | Verbalization | E2 headless invariance |
| Causal HUD | `brain/causal_hud.py` | **NO** | Declarative `agency_guard` | Tests |
| Continuous motor / navigation | `brain/navigation.py`, continuous-motor flag | **NO** to schema key | May bias locomotion toward goals | Can affect path without writing `choice_key` — document as separate channel |
| Study wrappers | `publication_finalization/scripts/run_publication_experiments.py` | **YES (control only)** | Force override after `run` | Labeled experimental |

## Grep notes (assignment sites)

Primary construction of the deliberation result:

- `brain/deliberation.py`: `choice_key=winner.key` inside `PrefrontalDeliberation.run`.

Other `choice_key=` occurrences are **data plumbing** (intention circuit copy, goal stack frames, memory records, prefetch predictions, test fixtures) — not alternate motor decision writers in the live tick path.

## Unit / smoke tests (commands)

```powershell
$env:CEREBRO_SKIP_PROCESS_GUARD="1"
.\.venv\Scripts\python.exe -m pytest tests/test_grounding.py tests/test_td_reward.py tests/test_affordance_map.py tests/test_demo_hud.py tests/test_s7_scale_motor_multi.py -q --tb=line
```

Results are recorded under `raw_results/motor_audit_E/pytest_agency.txt` when the audit script is executed.

## Limits

- Static audit ≠ exhaustive dynamic proof of all future code paths.
- Interactive LLM + continuous-motor combinations should be re-audited before strong safety claims.
- Do not equate `agency` metric with free will or consciousness.
