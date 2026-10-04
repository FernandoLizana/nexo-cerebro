# P5 — NEXO Cognitive QA · entrega

**Fecha:** 2026-08-19 · **Fase:** P5 · **Veredicto:** PASS  
**Tema:** Cognitive Personas, Individual Differences, Behavioral Diversity

---

## 1. Resumen ejecutivo

P5 introduce **CognitivePersona**: una configuración mecanística versionada y validada que modifica parámetros reales de NEXO (WM, atención, deliberación, BG, afecto) para producir **diversidad conductual** bajo mismo objetivo, misma web y mismo seed — **sin** reglas `persona → acción`.

**Evidencia:** 33 tests P5 PASS · v90 golden intacto · P4 opt-in preservado.

---

## 2. Estado recibido desde P4

| Entregable P4 | Estado en P5 |
|---------------|--------------|
| `Goal` / `TaskContext` | Preservado — persona no muta goal |
| `bind_task()` | Preservado |
| `goal_relevance` hooks | Extendido con `persona_modifiers` |
| Oracle isolation | Preservado |
| P3 perception | Preservado + persona perception override |
| Default behavior | Sin `bind_persona()` = P4 |

---

## 3. Arquitectura

```text
configs/nexo_qa/personas/*.yaml
        ↓
load_persona → validate → CognitivePersona
        ↓
bind_persona(rt, persona, world=...)
        ↓
apply_persona_to_config + PersonaStateProcess
        ↓
TaskGoalProcess → PFC (+ literacy/confidence) → BG (+ distract/risk/explore)
        ↓
BrowserWorld (P3) → outcomes → frustration/fatigue state
```

---

## 4. CognitivePersona

- **Schema version:** 1  
- **Traits:** 15 campos funcionales (WM, distractibility, risk, …)  
- **State:** `PersonaState` dinámico (frustration, fatigue, stagnation)  
- **Hash:** `config_hash()` en cada persona  
- **Docs:** `P5_PERSONA_MODEL.md`, `P5_TRAIT_STATE_MODEL.md`

---

## 5. Mechanistic mapping

Tabla completa en `P5_MECHANISTIC_MAPPING.md` y `artifacts/p5/mechanistic_mapping.json`.

Punto único de aplicación: `nexo_qa/personas/runtime.py::apply_persona()`.

---

## 6. Presets

8 perfiles en `configs/nexo_qa/personas/`:

`baseline`, `low_wm`, `high_distractibility`, `risk_averse`, `impatient`, `fatigued`, `novice_digital`, `expert_digital`

**No son calibración humana** — perfiles de ingeniería.

---

## 7. Web Lab P5

7 escenarios + manifest `persona_scenarios.json`. Ver `P5_WEB_LAB.md`.

---

## 8. Tests

`tests/test_p5_personas.py` — 33 tests cubriendo validación, mapping, diversidad, web lab, regresión, oracle isolation, anti action-rules.

---

## 9. Regresión

| Gate | Resultado |
|------|-----------|
| v90 trajectory_hash | `77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c` ✓ |
| P0–P4 | Preservados (persona opt-in) |
| Direct persona→action rules | None found |

---

## 10. Artefactos

`artifacts/p5/`: preflight, persona_schema, mechanistic_mapping, preset_manifest, effect_audit, paired_runs, sensitivity_analysis, test_results, regression, performance, quality_gate, behavioral_fingerprints.

Generador: `scripts/generate_p5_artifacts.py`

---

## 11. Archivos creados

```text
nexo_qa/personas/          (models, validation, mapping, loader, runtime, conventions, effects, runner)
configs/nexo_qa/personas/  (8 YAML presets)
tests/test_p5_personas.py
tests/fixtures/web_lab/    (P5 HTML + persona_scenarios.json)
docs/cognitive_qa/P5_*.md  (13 docs)
docs/cognitive_qa/adr/ADR-0006-*.md
scripts/generate_p5_artifacts.py
artifacts/p5/
```

## 12. Archivos modificados

```text
nexo/prefrontal/deliberation.py      — persona_modifiers in PFC
nexo/core/process_executive.py       — persona_modifiers in BG
nexo_qa/goals/runtime.py             — action_salience injection
nexo_qa/browser/browser_world.py     — action_salience_map()
nexo_qa/testing/__init__.py            — bind_persona export
nexo_qa/__init__.py                  — phase P5
tests/test_p0_nexo_qa_import.py      — assert P5
.github/workflows/tests.yml          — optional P5 step
```

---

## 13. Quality Gate

Ver `artifacts/p5/quality_gate.json` — **verdict: PASS**

---

## 14. Handoff P6

P6 construirá métricas QA (NCFS, failure taxonomy, certificates) sobre traces enriquecidos con persona_id, traits, state, actions, frustration, fatigue.

Ver `P5_HANDOFF_TO_P6.md`.

---

## 15. Limitaciones

- Diversidad conductual depende de escenario/seed.
- Personas no calibradas a humanos (P9).
- Fatigue/frustration dynamics mínimas.
- Population engine completo → P7.

---

## 16. Preguntas Quality Gate

| Pregunta | Respuesta |
|----------|-----------|
| ¿NEXO v90 sigue funcionando? | YES |
| ¿P1–P4 preservados? | YES |
| ¿Existe CognitivePersona? | YES |
| ¿Traits/states separados? | YES |
| ¿Traits → mecanismos reales? | YES |
| ¿Reglas persona→acción? | NO |
| ¿Default persona ≈ P4? | YES |
| ¿Misma tarea+seed+persona distinta → conducta distinta posible? | YES |
| ¿Human-calibrated? | NO |
| ¿Persona bypass seguridad? | NO |
| ¿Listos para P6? | YES |
