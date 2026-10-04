# P5 — Performance Baseline

| Operation | Overhead |
|-----------|----------|
| load_preset | ~1ms YAML parse |
| apply_persona_to_config | O(traits), one-time |
| PersonaStateProcess | 1 tick period, lightweight |
| Matrix cell (8 ticks) | dominated by browser/runtime |

Persona does not duplicate tick cost arbitrarily.

Artifact: `artifacts/p5/performance.json`
