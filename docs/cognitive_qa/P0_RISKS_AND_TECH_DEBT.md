# P0 — Risks and technical debt

Separates **preexisting NEXO debt** from **Cognitive QA debt**. P0 introduced no product QA logic.

## Preexisting (do not “clean” in P0)

### P0-RISK-001 · COUPLING · CRITICAL

Deliberation and drives know RoomWorld verbs (`eat`/`rest`/`flee`/…).  
Evidence: `nexo/prefrontal/deliberation.py` `ROOM_ACTION_SCHEMAS`; `nexo/homeostasis/drives.py` `action_bias`.  
Impact: BrowserWorld cannot be a drop-in.  
Phase: P1. Not P0.

### P0-RISK-002 · COUPLING · CRITICAL

`world_factory.create_world` returns `RoomWorld`; v90 `WorldDemoFacade` still uses `apply_action` while sharing `brain.world`.  
Evidence: `nexo/demo/world_factory.py`, `nexo/demo/world_demo_facade.py`.  
Impact: dual motor authority.  
Phase: P1.

### P0-RISK-003 · COUPLING · CRITICAL

`world2d_actions.LEGACY_TO_INTEGRATED` collapses drink→rest, unknown→explore.  
Evidence: `nexo/demo/world2d_actions.py`.  
Impact: semantic loss; v90 12-tick golden is 12× `explore`.  
Phase: P1 (adapter, not silent remap).

### P0-RISK-004 · ARCHITECTURE · HIGH

Two writers of action: nexo `action.selected` vs brain `choice_key`. Static agency audit only covers `brain/deliberation.py`.  
Evidence: `nexo/decision_audit.py`; `EnhancedBasalGangliaProcess`.  
Phase: P1 observability; do not weaken PFC thesis.

### P0-RISK-005 · OBSERVABILITY · MEDIUM

Causal certificate lacks percepts, candidates, post-state. `causal_parent` unused.  
Evidence: `nexo/behavioral/causal_certificate.py`; `nexo/core/events.py`.  
Phase: P2+ Cognitive Failure Certificate wrapping, not rewriting.

### P0-RISK-006 · CONFIGURATION · LOW

Pillow pin vs requirements.txt `<12` vs pyproject `<13`.  
Evidence: `P0_DEPENDENCY_BASELINE.md`.  
Phase: later hygiene. Not P0.

### P0-RISK-007 · DOCUMENTATION · LOW

`OPEN_ISSUES.md`, `NEXO_ARCHITECTURAL_DESIGN.md`, `ENVIRONMENT.json`, `COMMIT_HASH.txt` are stale.  
Phase: docs later. P0 recorded live git hash in artifacts.

### P0-RISK-008 · TESTING · MEDIUM

CI runs a subset, not 605 tests. GPU/web/external tests need classification.  
Phase: keep CI subset; full suite is P0 baseline artifact.

### P0-RISK-009 · REPRODUCIBILITY · LOW

`RoomWorld.apply_action` uses `uuid4` for `encoded_memory`. Trajectory of **actions** is deterministic; episode ids are not.  
Evidence: `nexo/demo/room_scenario.py` L84.  
STRICT invariant = `trajectory_hash`, not episode ids.

### P0-RISK-010 · LEGACY · HIGH

91/100 roadmap items `unable_to_verify`. Completing that map is not a QA prerequisite.  
Phase: never block Cognitive QA on it.

### P0-RISK-011 · DUPLICATION · MEDIUM

`nexo/core/clock.py` vs `nexo/simulation_clock.py`; hippo vs SQLite vs promoted `hippo_*`.  
Phase: do not merge stores in P0/P1.

### P0-RISK-012 · PERFORMANCE · INFO

v90 12 ticks ≈ 3.4–3.7 s including startup (~3.25 ticks/s) on this machine. No RAM sample (`psutil` undeclared).

## Cognitive QA debt (must not start yet)

- No Environment Protocol.
- No ActionSchema.
- No BrowserWorld.
- No personas.
- Feature flag not wired into `IntegratedRuntimeConfig` (intentional).

## Categories index

COUPLING: 001–003 · DUPLICATION: 011 · LEGACY: 010 · CONFIGURATION: 006 · TESTING: 008 · PERFORMANCE: 012 · REPRODUCIBILITY: 009 · OBSERVABILITY: 005 · ARCHITECTURE: 004 · DOCUMENTATION: 007
