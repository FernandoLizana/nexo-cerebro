# ADR-0006 — Cognitive Personas as Mechanistic Configuration

**Status:** Accepted  
**Date:** 2026-08-19  
**Phase:** P5

## Context

P4 established declarative goals and task context. P5 must introduce **individual cognitive differences** without demographic stereotypes or direct action scripting.

## Problem

Label-based personas (`if persona == "impatient": click X`) would violate agency audit and fail to demonstrate mechanistic causality.

## Decision

1. **`CognitivePersona`** is a versioned, validated, serializable trait profile — not a biography.
2. **Traits are immutable** during a run; **PersonaState** (frustration, fatigue, confidence) is dynamic.
3. **Single application boundary:** `apply_persona()` / `bind_persona()` in `nexo_qa/personas/runtime.py`.
4. **Mechanistic mapping** documented in `MECHANISTIC_MAP` and applied via `apply_persona_to_config()`.
5. **Core hooks** (minimal): `persona_modifiers` in PFC deliberation and BG scoring; optional WM/perception overrides.
6. **Presets live in YAML** under `configs/nexo_qa/personas/` — core knows traits, not marketing names.
7. **Default:** no persona specified → P4 behavior unchanged (`nexo_qa.__enabled_by_default__ = False`).

## Trait vs State

| Kind | Examples | Mutability |
|------|----------|------------|
| Trait | `working_memory_capacity`, `risk_aversion` | Fixed at bind |
| State | `current_frustration`, `current_fatigue` | Updated each tick |

## Mechanistic Mapping (summary)

See `docs/cognitive_qa/P5_MECHANISTIC_MAPPING.md` for full table.

## Application Boundary

```text
YAML preset → load_persona → validate → apply_persona_to_config → PersonaStateProcess
```

## Reproducibility

Same persona + seed + goal + environment → stable behavior. Different persona + same seed → isolates trait effect in sensitive scenarios.

## No Direct Action Rules

Static scan in `test_no_direct_persona_action_rules_in_package` forbids persona-conditioned action selection in `nexo_qa/personas/`.

## No Demographic Stereotyping

Presets use mechanistic names (`low_wm`, `risk_averse`). No clinical or age-based labels.

## Human Calibration Deferred

P9 will validate against humans. P5 profiles are **engineering defaults**.

## Alternatives Considered

- **Hardcoded persona branches in BrowserWorld** — rejected (oracle-like).
- **Full population engine** — deferred to P7.

## Known Limitations

- Behavioral diversity not guaranteed in all scenarios/seeds.
- `fatigue_rate_modifier` uses lightweight dynamics, not full physiology.
- Memory-demand scenario depends on WM encoding fidelity.

## Implications

- **P6:** metrics and failure taxonomy on persona-enriched traces.
- **P7:** population matrices at scale.
- **P9:** human calibration of trait ranges.
