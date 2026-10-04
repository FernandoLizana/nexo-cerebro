# P7 — NEXO Cognitive QA · entrega

**Fecha:** 2026-08-19 · **Fase:** P7 · **Veredicto:** PASS  
**Tema:** Population Engine, Cognitive Stress Testing, Cohort Aggregation

---

## 1. Resumen ejecutivo

P7 escala el análisis P6 de **1 run** a **poblaciones reproducibles**:

```text
PopulationSpec → Planner → RunPlan[] → Runner → P6 × N → Aggregator → Report
```

**Evidencia:** 30 tests P7 PASS · 30 tests P6 PASS · P0 PASS · `artifacts/p7/quality_gate.json` PASS

---

## 2. Estado recibido desde P6

- `analyze_raw_trace` / `capture_run_trace` como fuente única por run
- NCFS, EHFP, CRS, failure taxonomy, certificates
- Fixtures offline en `tests/fixtures/cognitive_qa/`

---

## 3. Arquitectura

```text
nexo_qa/population/
  models.py       PopulationSpec, CohortSpec, RunPlan, RunExecutionRecord
  validation.py   run count guards
  seeds.py        deterministic child seeds + run IDs
  planner.py      PopulationPlanner, PopulationPlan
  runner.py       PopulationRunner (trace_fixture | mock_world)
  state.py        checkpoint / resume
  aggregator.py   distributions, cohort comparisons
  clustering.py   failure clusters, rare critical
  stress.py       CognitiveStressTest, wm_sweep
  reporting.py    JSON / MD / CSV
  cli.py          plan | run | aggregate
```

Configs: `configs/nexo_qa/populations/baseline_population.yaml`, `wm_stress_population.yaml`

---

## 4. PopulationSpec y CohortSpec

Versionados (`schema_version: 1`), hash `spec_hash`, validación antes de planificar. Cohortes = segmentos experimentales, no demografía.

---

## 5. Seed strategy

Hash-based, reordering-invariant. Cambiar paralelismo **no** cambia seeds ni run IDs.

---

## 6. Runner

- Bounded parallelism (máx. 4 workers)
- Aislamiento por run (MockWorld / fixture)
- `FAILED_INFRASTRUCTURE` vs `FAILED_TASK` separados
- Solo infra reintenta; task failure no
- Resume idempotente vía `population_state.json`
- Cache de runs completados

---

## 7. Agregación

Distribuciones (mean, median, p10–p90), denominadores explícitos, comparación entre cohortes, failure clusters con drill-down a certificates.

**Disclaimer:** distribuciones de simulación NEXO — no población humana.

---

## 8. Cognitive Stress Testing

`CognitiveStressTest` + `wm_sweep()` — one-factor-at-a-time cohorts por nivel de trait P5.

---

## 9. Tests

`tests/test_p7_population.py` — 30 tests.

```bash
python -m pytest tests/test_p7_population.py -q
python -m pytest tests/test_p6_cognitive_qa.py tests/test_p0_nexo_qa_import.py -q
```

---

## 10. Quality Gate

Ver `artifacts/p7/quality_gate.json` — **PASS**

Generar artefactos:

```bash
python scripts/generate_p7_artifacts.py
```

---

## 11. Regresión

| Fase | Preservada |
|------|------------|
| P0–P6 | YES |
| v90 golden hash | YES (sin cambios al core NEXO) |

---

## 12. Handoff P8

P8 recibe: `PopulationSpec`, `ConditionSet`, paired seeds, runner, aggregator, métricas P6.

Ver `docs/cognitive_qa/P7_HANDOFF_TO_P8.md` y ADR-0008.

---

## 13. Veredicto final (checklist)

| Pregunta | Respuesta |
|----------|-----------|
| ¿NEXO v90 sigue funcionando? | YES |
| ¿P1–P6 preservados? | YES |
| ¿PopulationSpec / CohortSpec? | YES |
| ¿RunPlans deterministas? | YES |
| ¿Parallelism cambia seeds? | NO |
| ¿Dry-run? | YES |
| ¿Run explosion guard? | YES |
| ¿Resume idempotente? | YES |
| ¿Distribuciones + percentiles? | YES |
| ¿Drill-down a certificates? | YES |
| ¿Cognitive Stress Testing? | YES |
| ¿Representan población humana? | NO |
| ¿Infra distribuida requerida? | NO |
| ¿Listos para P8? | YES |

**VEREDICTO: PASS**
