# P5 — Overview

**Phase:** P5 · **Theme:** Cognitive Personas / Individual Differences

## Mission

Same goal + same web + same seed + **different mechanistic profile** → measurably different cognition and behavior.

## Architecture

```text
CognitivePersona (traits, immutable)
        ↓
apply_persona() / bind_persona()
        ↓
┌───────────────────────────────────────┐
│ WM capacity │ Perception limits       │
│ PFC inhibition │ persona_modifiers    │
│ PersonaStateProcess (dynamic state)   │
└───────────────────────────────────────┘
        ↓
TaskGoalProcess (unchanged) → PFC → BG → BrowserWorld
```

## Module Layout

```text
nexo_qa/personas/
  models.py      — CognitivePersona, PersonaTraits, PersonaState
  validation.py  — reject NaN, unknown fields, bad ranges
  mapping.py     — MECHANISTIC_MAP, apply_persona_to_config
  loader.py      — YAML presets
  runtime.py     — apply_persona, bind_persona, PersonaStateProcess
  conventions.py — digital literacy UI priors
  effects.py     — PersonaEffectAudit
  runner.py      — small task×persona×seed matrix
```

## Legacy Safety

Without `bind_persona()`, NEXO behaves as P4. `nexo_qa.__phase__ = "P5"`, `__enabled_by_default__ = False`.

## Quality Gates

See `artifacts/p5/quality_gate.json`.
