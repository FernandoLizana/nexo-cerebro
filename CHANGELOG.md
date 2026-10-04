# Changelog

## [0.2.0] — 2026-08-04

### Reproducibilidad científica

- Paquete `nexo/` con semillas centralizadas, configuraciones, estadística, esquema de resultados
- `python -m scripts.verify_artifact` — verificación única
- Condiciones explícitas: `baseline`, `roadmap100_full`, ablaciones con hash SHA-256
- Fix `multimodal_similarity` dim mismatch (128 vs 384)
- Fix colección pytest (excluir `artifacts/`, `publication_finalization/`)
- Métricas agency extendidas; `legacy_agency_score` conservado
- Auditorías en `reports/` y trazabilidad roadmap 100

### Breaking / metodológico

- `full` documentado como alias de **baseline** (no activa roadmap100)
- Usar `roadmap100_full` para dinámicas completas

## [0.1.x] — histórico

- Roadmap 100 bloques A–K implementados en `brain/`
- Batería E1 GPU parcial
