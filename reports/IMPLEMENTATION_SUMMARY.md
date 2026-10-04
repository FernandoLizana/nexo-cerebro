# Resumen de implementación — refactor reproducibilidad NEXO

**Fecha:** 2026-08-04

## Qué se corrigió

1. Colección pytest rota por tests duplicados en `artifacts/` → `pyproject.toml` norecursedirs
2. Crash headless `multimodal_similarity` (128 vs 384)
3. RNG deliberación atado a `age_ticks` → `brain.random_streams.decision`
4. Ambigüedad `full` vs roadmap100 → condiciones nombradas + hash
5. Falsos positivos auditoría `failed_choice_key` → AST preciso
6. Logs "libre albedrío" → "selección PFC" en `agent_loop.py`

## Qué no se pudo corregir de forma segura

1. Inicializar git / commit real (workspace sin `.git`)
2. Suite completa 308 tests en CI local (tiempo; ejecución parcial)
3. Migración completa RNG en todos los módulos legacy
4. Extracción total dominio demo de `ACTION_SCHEMAS`
5. Batería paper E1–E8 completa (datos históricos parciales intactos)
6. Refuerzo hábitos solo por outcome (flag `legacy_reinforce_on_selection` documentado)

## Archivos creados (principales)

- `nexo/` — random_streams, experiment_conditions, result_schema, statistics, decision_port, agency_metrics, decision_audit, behavioral_tasks, environment, paths
- `configs/` — experiment_conditions, battery_*, model/*
- `schemas/experiment_result.schema.json`
- `scripts/verify_artifact.py`, `scripts/build_release_artifact.py`
- `experiments/run_battery.py`, `experiments/run_sensitivity_analysis.py`
- `tests/test_reproducibility.py`, `test_experiment_conditions.py`, `test_statistics.py`, `test_decision_audit.py`
- `reports/*` (auditorías)
- `roadmap/roadmap100_traceability.json`
- `docs/ROADMAP100_TRACEABILITY.md`
- `README_REPRODUCCION.md`, `KNOWN_LIMITATIONS.md`, `pyproject.toml`, `LICENSE`, `CITATION.cff`
- `.github/workflows/tests.yml`
- `brain/scenarios/home_demo.py`

## Archivos modificados (principales)

- `brain/mind.py` — seed, random_streams, sim_clock
- `brain/deliberation.py` — RNG, agency_metrics, DecisionPort, confidence margin
- `brain/imagination.py`, `brain/episodic_context.py`
- `brain/experiment_flags.py`, `brain/agent_loop.py`
- `experiments/run_batch.py`
- `README.md`, `requirements.txt`, `CHANGELOG.md`

## Tests agregados

23 en subconjunto verify (ver TEST_EXECUTION_REPORT.md)

## Tests ejecutados (reales)

- verify subset: **23 passed, 0 failed**
- reproducibility: **7 passed**
- artifact verify: **pass**

## Resultados reales reproducibilidad

- same_seed: **true**
- different_seeds: **true**

## Problemas abiertos

Ver `reports/OPEN_ISSUES.md`

## Riesgos científicos

- Métricas legacy saturadas en E1 histórico
- Claims previos "61 passed" / "libre albedrío" en docs viejos
- Sin git para trazabilidad commit-resultado

## Próximos pasos

1. `git init` + commit + tag v0.2.0
2. Ejecutar suite completa 308 tests
3. Completar batería paper manual
4. Migrar RNG restantes
5. `python scripts/build_release_artifact.py`
