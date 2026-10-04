# Reporte de ejecución de tests

**Fecha:** 2026-08-04  
**Python:** 3.11.0  
**Commit:** NO_GIT_REPOSITORY

## Recolección

| Métrica | Valor |
|---------|-------|
| Tests recopilados | **308** |
| Errores de colección | **0** (post `pyproject.toml` norecursedirs) |

Comando: `python -m pytest tests/ --collect-only -q`

## Subconjunto verificación CI (ejecutado)

Incluido en `python -m scripts.verify_artifact`:

| Archivo | Resultado |
|---------|-----------|
| `tests/test_reproducibility.py` | 7 passed |
| `tests/test_experiment_conditions.py` | 4 passed |
| `tests/test_statistics.py` | 3 passed |
| `tests/test_validation_dynamics.py` | 7 passed |
| `tests/test_decision_audit.py` | 1 passed |
| **Total verify subset** | **23 passed, 0 failed** (67s) |

## Suite completa (`tests/`)

**Estado:** ejecución completa no finalizada en esta sesión (suite ~308 tests; estimado >15 min por simulaciones headless).

Progreso parcial observado en `reports/pytest-output.txt`: ~23% antes de interrupción.

**Recomendación:** ejecutar localmente:

```bash
python -m pytest tests/ -q --tb=short 2>&1 | tee reports/pytest-output.txt
python -m pytest tests/ --junitxml=reports/pytest-report.xml
```

## Tests nuevos agregados

- `tests/test_reproducibility.py`
- `tests/test_experiment_conditions.py`
- `tests/test_statistics.py`
- `tests/test_decision_audit.py`

## Fix aplicado durante auditoría

- `brain/episodic_context.py` — alineación dimensional en `multimodal_similarity` (128 vs 384)
