# ADR-0001 — Cognitive QA as an extension of NEXO

**Status:** Accepted (P0 freeze, 2026-08-18)

**Date:** 2026-08-18

**Baseline:** `integrated_v90` · git `3a0233c3c4fe504bcad5b545d7bbc43d0e6c2608`

## Context

NEXO v90 is a scientific cognitive runtime with two stacked implementations:

- **Integrated core:** `nexo/integrated_runtime.py` → `CognitiveScheduler` + duck-typed worlds.
- **Legacy brain:** `brain/mind.py` (`InfantApeBrain`) + `brain/agent_loop.py` (`NeuralAgentLoop`).

The next product direction is **NEXO Cognitive QA**: agents that interact with applications and websites as cognitively differentiated users. That work must not replace the v90 scientific line (memory unification, causal certificates, agency audit, batteries, replication, publication).

## Decision

NEXO Cognitive QA will be developed as a **decoupled extension**, not as a rewrite of the Cognitive Core.

```text
NEXO
├── Cognitive Core          (nexo/, brain/ — KEEP)
├── Experimental / Science  (experiments/, configs/battery/, replication — KEEP)
└── Cognitive QA            (nexo_qa/ — grow later; disabled by default)
```

P0 created only:

- `nexo_qa/__init__.py`
- `tests/nexo_qa/test_p0_import.py`

No BrowserWorld, Playwright, Selenium, personas, or friction scores.

A future feature flag `cognitive_qa.enabled: false` is **specified** in `P0_HANDOFF_TO_P1.md` and **not wired** into `IntegratedRuntimeConfig` in P0, so historical YAML profiles cannot accidentally activate QA.

## Consequences

- Scientific experiments continue to use `configs/nexo/integrated_v90.yaml` unchanged in semantics.
- Cognitive QA code must not write `choice_key` (legacy) or bypass `MotorExecutionProcess` / `ActionGate` without an explicit, audited adapter.
- World coupling identified in P0 is documented, not “fixed” in P0.
- Later phases wrap the existing agent↔world duck type instead of forking a second brain.

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Rewrite `nexo/` around BrowserWorld | Destroys v90 reproducibility and H1/H2 evidence. |
| Put QA inside `brain/agent_loop.py` | Dual motor authority already exists; adding a third loop is worse. |
| New standalone repo | Would fork the cognitive core and lose batteries, certificates, and agency audit. |

## Risks

- Developers may still “clean up” RoomWorld action names during P1. That is a behavioral change; it needs a golden baseline comparison (`artifacts/baseline/p0/reproducibility/`).
- `nexo_qa` living at repo root could be imported by accident. Mitigation: `__enabled_by_default__ = False` and no runtime registration in P0.
