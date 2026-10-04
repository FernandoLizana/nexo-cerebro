# P5 — Trait / State Model

## Traits (immutable per run)

Functional parameters: WM capacity, distractibility, risk aversion, patience, digital literacy, etc.

Stored in `CognitivePersona.traits` (frozen dataclass fields).

## State (dynamic)

`PersonaState` in `nexo_qa/personas/models.py`:

| Field | Updated by |
|-------|------------|
| `current_frustration` | failures, stagnation, loops |
| `current_fatigue` | ticks, frustration, fatigue_rate_modifier |
| `current_confidence` | initialized from semantic_confidence |
| `ticks_without_progress` | goal progress stagnation |
| `repeated_action_count` | action repetition |

## Process

`PersonaStateProcess` emits:

- `persona.state` — trace payload with persona_id + state dict
- `affect.updated` — frustration → cognitive affect
- `homeostatic.fatigue_changed` — minimal fatigue delta

## Separation Test

Trait `working_memory_capacity` on persona object never mutates; only `PersonaState` changes during run.
