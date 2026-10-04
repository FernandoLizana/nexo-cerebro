# Resumen de implementación — cierre reproducibilidad NEXO

**Fecha:** 2026-08-04  
**Versión artefacto:** 0.3.0  
**SHA256:** `768ced4743918a227e572d547764f639937faefba7bfcbcb98de0b83a55aa6f2`

---

## Scripts principales

| Script | Versión | Función |
|--------|---------|---------|
| `scripts/build_release_artifact.py` | 2.0.0 | ZIP con validación previa/posterior |
| `scripts/verify_artifact.py` | 2.1.0 | Verificación workspace; reporte siempre |
| `scripts/verify_packaged_artifact.py` | 1.0.0 | Extrae ZIP, smoke, verify |
| `scripts/check_dependency_consistency.py` | — | Lock vs pyproject |
| `scripts/validate_roadmap_traceability.py` | — | 100 IDs, estados honestos |
| `scripts/generate_repository_inventory.py` | — | Inventario JSON |

---

## Correcciones clave en esta sesión

1. **`build_release_artifact.py`:** rutas relativas; exclusión por nombre; incluye `data/curriculum/`; excluye `experiments/results/` y `data/brain_state/`; fix `UnboundLocalError`; validación directorios en ZIP.
2. **`verify_packaged_artifact.py`:** PYTHONPATH en extracción; skip escaneo personal en scripts de auditoría.
3. **`brain/agent_loop.py`:** `sleep_arch` (fix smoke `AttributeError`).
4. **`nexo/experiment_conditions.py`:** flags core clasificados (`enable_verify`, `enable_consciousness`, etc.).
5. **`KNOWN_LIMITATIONS.md`:** rutas personales redactadas.

---

## Resultados smoke (`results/smoke/`)

5 archivos JSON válidos:

- `baseline_legacy_seed_42.json`
- `roadmap100_full_v1_seed_42.json`
- `roadmap100_full_v1_seed_99.json`
- `roadmap100_no_binding_v1_seed_42.json`
- `roadmap100_no_pfc_v1_seed_42.json`

Campos: `seed`, `condition`, `flags`, `config_hash`, `commit`, `trajectory_hash`, `metrics`.

---

## Trazabilidad Roadmap 100

- 100 identificadores únicos (`R100-001` … `R100-100`)
- 9 entradas con evidencia de código/tests (`unit_tested`)
- 91 entradas `unable_to_verify` (sin inventar módulos)
- Validador: `python scripts/validate_roadmap_traceability.py` — 0 errores

---

## Verificación empaquetada (autoritativa para entrega)

```json
{
  "status": "pass",
  "verification_scope": "packaged_artifact_verification",
  "smoke_runs_completed": 5,
  "verify_artifact_status": "pass",
  "personal_paths_detected": []
}
```

---

## Comandos para reproducir

```powershell
cd .
python -m pip install -e ".[dev]"
python -m scripts.check_dependency_consistency
python -m pytest tests/test_reproducibility.py tests/test_experiment_conditions.py tests/test_statistics.py tests/test_decision_audit.py tests/test_smoke_results.py -q
python -m experiments.run_smoke_experiments
python -m scripts.verify_artifact
python scripts/build_release_artifact.py
python -m scripts.verify_packaged_artifact
python scripts/validate_roadmap_traceability.py
```

---

## Pendiente

Ver `reports/OPEN_ISSUES.md`.
