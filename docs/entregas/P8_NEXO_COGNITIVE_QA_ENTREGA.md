# P8 — NEXO Cognitive QA · entrega

**Fecha:** 2026-08-19 · **Fase:** P8 · **Veredicto:** PASS  
**Tema:** Cognitive Chaos Testing, Interruptions, Environmental Perturbations

---

## 1. Resumen ejecutivo

P8 introduce perturbaciones ambientales **controladas y reproducibles** con diseño **pareado**:

```text
same task + same persona + same seed
     BASELINE  vs  PERTURBED → PairedChaosDelta
```

**Evidencia:** 32 tests P8 PASS · 92 tests P0–P8 PASS · `artifacts/p8/quality_gate.json` PASS

---

## 2. Arquitectura

```text
nexo_qa/chaos/
  models.py          PerturbationSpec, ChaosSpec, PairedChaosDelta
  validation.py      environment-only guards
  triggers.py        deterministic trigger evaluation
  controller.py      PerturbationController
  perturbed_world.py ChaoticMockWorld
  pairs.py           pair invariants + deltas
  planner.py         ChaosPlanner (paired RunPlans)
  runner.py          ChaosRunner + resume + baseline cache
  aggregation.py     population chaos + cohort sensitivity
  reporting.py       chaos_report JSON/MD/CSV
  offline.py         analyze_pairs / analyze_chaos_directory
  web_lab.py         scenario registry + HTML fixtures
```

Config: `configs/nexo_qa/chaos/paired_baseline.yaml`

---

## 3. Perturbation types implementados (8+)

INTERRUPTION, LATENCY, TRANSIENT_ERROR, SESSION_EXPIRY, VISUAL_CHANGE, MODAL_DISTRACTION, FEEDBACK_DELAY, CONTROL_DISABLE (+ NETWORK_LIKE_FAILURE in model)

---

## 4. Paired design

- `pair_id` + `derive_paired_seed()` — seed no depende de condition
- `validate_pair_invariants()` → VALID / INVALID_PAIR / INCOMPATIBLE_PAIR
- Missing metrics ≠ 0

---

## 5. Tests

```bash
python -m pytest tests/test_p8_chaos.py -q
python scripts/generate_p8_artifacts.py
```

---

## 6. Quality Gate

Ver `artifacts/p8/quality_gate.json` — **PASS**

---

## 7. Veredicto checklist

| Pregunta | Respuesta |
|----------|-----------|
| ¿P7 preservado? | YES |
| ¿PerturbationSpec versionado? | YES |
| ¿PerturbationController separado del core? | YES |
| ¿Perturbaciones solo en environment? | YES |
| ¿Diseño pareado? | YES |
| ¿Same task/persona/seed? | YES |
| ¿Paired delta? | YES |
| ¿Interruption/Latency/Error/Session/Visual/Modal/Feedback? | YES |
| ¿Trazas de perturbación? | YES |
| ¿Human calibrated? | NO |
| ¿Listos para P9? | YES |

**VEREDICTO: PASS**
