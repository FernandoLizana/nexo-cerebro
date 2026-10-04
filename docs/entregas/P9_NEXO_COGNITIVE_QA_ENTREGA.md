# P9 — NEXO Cognitive QA · entrega

**Fecha:** 2026-08-19 · **Fase:** P9 · **Veredicto:** CONDITIONAL PASS — HUMAN DATA REQUIRED  
**Tema:** Human Calibration Lab, Behavioral Correlation, Model Validation

---

## 1. Resumen ejecutivo

P9 construye el **Human Calibration Lab** completo: protocolos, captura, datasets versionados, alineamiento comportamental, HBC, validación NCFS/CRS/EHFP, registro de calibración, dominio OOD, Model/Data Cards.

**No hay datos humanos reales aún** — el pipeline se valida con fixtures sintéticos etiquetados.

**Evidencia:** 31 tests P9 PASS · 123 tests P0–P8 PASS · `artifacts/p9/quality_gate.json`

---

## 2. Arquitectura

```text
nexo_qa/human_lab/
  models.py           HumanStudySpec, HumanInteractionEvent, HumanCalibrationDataset, …
  events.py           normalization (semantic categories)
  privacy.py          pseudonymization, redaction, delete_participant
  dataset.py          HumanCalibrationDataset builder
  alignment.py        BehavioralAlignmentAnalyzer
  hbc.py              HBC components
  matched.py          task version matching
  split.py            grouped train/holdout
  calibration/        engine, ncfs/crs/ehfp-hfp, domain, registry
  taxonomy_validation.py, certificate_review.py, perturbation_alignment.py
  reporting.py, cards.py, synthetic.py
```

Ethics: `docs/cognitive_qa/human_lab/*.md`  
Config: `configs/nexo_qa/human_lab/pilot_study.yaml`

---

## 3. Human Data Status

```text
NO_HUMAN_DATA  ← actual
PILOT → CALIBRATION → VALIDATION → HOLDOUT_VALIDATED
```

---

## 4. HBC y alineamiento

Dimensiones: outcome, path, failure, recovery, perturbation.  
Composite con pesos documentados. Bootstrap CI cuando n lo permite.

---

## 5. EHFP → HFP

- EHFP sigue siendo proxy (no probabilidad) en P9
- HFP bloqueado: `hfp_claim_allowed = false`
- OOD bloquea claims fuera de `CalibrationDomain`

---

## 6. Tests

```bash
python -m pytest tests/test_p9_human_lab.py -q
python scripts/generate_p9_artifacts.py
```

---

## 7. Quality Gate

Ver `artifacts/p9/quality_gate.json` — **CONDITIONAL PASS**

---

## 8. Checklist

| Pregunta | Respuesta |
|----------|-----------|
| ¿P0–P8 preservados? | YES |
| ¿Human Calibration Lab? | YES |
| ¿HumanCalibrationDataset versionado? | YES |
| ¿HBC? | YES |
| ¿NCFS validado contra humanos? | NOT YET |
| ¿HFP calibrado? | NO |
| ¿OOD bloquea claims? | YES |
| ¿Datos humanos inventados? | NO |
| ¿Listos para P10? | YES |

**VEREDICTO: CONDITIONAL PASS — HUMAN DATA REQUIRED**
