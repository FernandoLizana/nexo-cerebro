# P5 — Mechanistic Mapping

| Trait | NEXO module | Parameter/state | Mechanistic effect | Test |
|-------|-------------|-----------------|-------------------|------|
| working_memory_capacity | WorkingMemoryBuffer | capacity | Limits active WM items | test_working_memory_mapping |
| attention_persistence | PerceptionConfig | max_focal_percepts | Focal attention slots | test_default_persona_preserves |
| visual_search_efficiency | PerceptionConfig | max_attended_percepts | Attention budget | test_default_persona_preserves |
| distractibility | EnhancedBasalGangliaProcess | persona_modifiers.distractibility | Boost high-salience low-goal actions | test_distractibility_modifiers_present |
| risk_aversion | EnhancedBasalGangliaProcess | persona_modifiers.risk_aversion | Penalize action_info.risk | test_risk_aversion_modifiers |
| exploration_tendency | EnhancedBasalGangliaProcess | persona_modifiers.exploration_tendency | Boost navigate/inspect/scroll | BG integration |
| impulsivity | PrefrontalDeliberator | pfc_inhibition_strength | Reduces PFC deliberation weight | impatient preset |
| digital_literacy | PrefrontalDeliberator | persona_modifiers + conventions | Scales goal relevance + UI priors | test_digital_literacy_convention_boost |
| semantic_confidence | PrefrontalDeliberator | persona_modifiers | Scales PFC score | novice vs expert |
| patience | PersonaStateProcess | persona_modifiers.patience | Stagnation threshold before frustration | test_patience_in_modifiers |
| frustration_tolerance | PersonaStateProcess | state.current_frustration | Failure response gain | test_frustration_state_updates |
| initial_fatigue | HomeostaticState | fatigue | Starting fatigue | fatigued preset |
| learning_rate_modifier | TDRewardSystem | learning_rate_scale | TD update scale | mapping only if td_system present |
| metacognitive_sensitivity | PrefrontalDeliberator | persona_modifiers | Inspect boost when high | deliberation hook |
| fatigue_rate_modifier | PersonaStateProcess | persona_modifiers | Fatigue accumulation rate | fatigued preset |

Machine-readable: `artifacts/p5/mechanistic_mapping.json`
