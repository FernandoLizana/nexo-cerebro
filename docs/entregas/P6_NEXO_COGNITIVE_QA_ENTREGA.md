# P6 — NEXO Cognitive QA · entrega

**Fecha:** 2026-08-19 · **Fase:** P6 · **Veredicto:** PASS  
**Tema:** Cognitive QA Metrics, Failure Taxonomy, Cognitive Failure Certificate

---

## 1. Resumen ejecutivo

P6 transforma ejecuciones cognitivas en **hallazgos QA estructurados, reproducibles y explicables**:

```text
RAW TRACE → normalize → observations → failures → episodes → metrics → certificates → report
```

**Evidencia:** 30 tests P6 PASS · análisis offline sin navegador · P5 preservado.

---

## 2. Arquitectura

```text
nexo_qa/analysis/     capture, normalize, offline pipeline
nexo_qa/failures/     taxonomy, classifier, episodes, severity, certificate
nexo_qa/metrics/      registry, core metrics, NCFS, EHFP, CRS, engine
nexo_qa/reporting/    summary, JSON + Markdown reports
```

Configs: `configs/nexo_qa/failures/v1.yaml`, `configs/nexo_qa/metrics/v1.yaml`

---

## 3. Scores (simulation-derived)

| Score | Rango | Nota |
|-------|-------|------|
| **NCFS** | 0–100 | NEXO Cognitive Friction Score — not human-calibrated |
| **EHFP** | 0–100 | Estimated Human Failure **Proxy** — **NOT a probability** |
| **CRS** | 0–100 | Cognitive Recovery Score |

---

## 4. Cognitive Failure Certificate

Schema v1 — extiende patrón causal certificate. Incluye goal, persona, perception, decision, outcome, failure, evidence. **Sin selectors ni secretos.**

---

## 5. Offline analysis

```python
from nexo_qa.analysis import analyze_run_file, analyze_run

result = analyze_run_file("tests/fixtures/cognitive_qa/distractor_loop_trace.json")
# result.json_report, result.certificates, result.metrics.ncfs
```

Raw artifacts inmutables — reanálisis versionado soportado.

---

## 6. Tests

`tests/test_p6_cognitive_qa.py` — 30 tests (normalization, taxonomy, classifier, certificates, NCFS/EHFP/CRS, pipeline, offline).

Fixtures: `tests/fixtures/cognitive_qa/*.json`

---

## 7. Quality Gate

Ver `artifacts/p6/quality_gate.json` — **PASS**

---

## 8. Handoff P7

P7 recibe: single-run metrics, failure taxonomy, certificates, persona_id, seed, run summary, versioned scores, raw trace compatibility.

Ver `docs/cognitive_qa/P6_HANDOFF_TO_P7.md`.

---

## 9. Preguntas Quality Gate

| Pregunta | Respuesta |
|----------|-----------|
| ¿P5 preservado? | YES |
| ¿Taxonomía versionada? | YES (failures-v1) |
| ¿Evidencia en trace? | YES |
| ¿Certificado sin selectors? | YES |
| ¿NCFS human-calibrated? | NO |
| ¿EHFP es probabilidad? | NO |
| ¿Análisis offline? | YES |
| ¿Listos para P7? | YES |
