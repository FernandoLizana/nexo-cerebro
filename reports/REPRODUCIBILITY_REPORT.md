# Reporte de reproducibilidad

**Fecha:** 2026-08-04  
**Verificación:** `python -m scripts.verify_artifact` → **status: pass**

## Semillas

| Prueba | Resultado |
|--------|-----------|
| Misma semilla (42), 6 ticks × 2 | **Hash idéntico** |
| Semillas 42 vs 99 | **Hashes distintos** |

Hashes (SHA-256 trayectoria):

- seed=42: `3db19e6d33412c9410f097d39514086e92c7ab8f2ee504142b30fe3cf97a9e09`
- seed=99: `7246c95dbdfb8628d068978bf3fbc7966884c586b8e18bfa73340b1ca0783998`

## Configuraciones

| Condición | config_hash (prefix) |
|-----------|---------------------|
| baseline | `b7e2ce7069787bc2...` |
| roadmap100_full | `a45a991bb8e4f312...` |
| enable_* true en roadmap100 | **91** flags |

## RNG

- Centralizado: `nexo.random_streams.RandomStreams`
- Deliberación: ya no usa `default_rng(age_ticks)` (test inspección código)
- Residual: `memory_store`, `regions`, `lifecycle` spawn — ver OPEN_ISSUES

## Metadatos

- `ENVIRONMENT.json` generado
- `COMMIT_HASH.txt` = `NO_GIT_REPOSITORY`

## Comandos

```bash
python -m pytest tests/test_reproducibility.py -q
python -m scripts.verify_artifact
```
