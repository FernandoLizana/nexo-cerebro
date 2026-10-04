# Problemas abiertos

**Actualizado:** 2026-08-04 (cierre reproducibilidad)

| ID | Severidad | Descripción | Acción sugerida |
|----|-----------|-------------|-----------------|
| O1 | Alta | Sin repositorio git | `git init`; commit; actualizar metadatos |
| O2 | Media | Suite 323 tests no ejecutada completa | `pytest tests/ -q` local/CI |
| O3 | Media | RNG legacy en memory_store, regions, archetype_cards | Migrar a RandomStreams |
| O4 | Media | Batería E1–E8 incompleta | Ejecución manual fuera de CI |
| O5 | Baja | 91/100 mejoras roadmap sin trazabilidad verificable | Mapear desde docs originales cuando existan |
| O6 | Baja | verify_packaged con `--skip-install` en verificación local | CI debe usar instalación pip completa |
| O7 | Baja | JUnit parser en verify_artifact reporta tests_collected=0 | Mejorar parseo XML |
| O8 | Info | Licencia MIT — decisión pendiente | Ver `reports/LICENSE_DECISION_REQUIRED.md` |

## Criterios aceptación pendientes

- [ ] Suite completa 323 green documentada
- [ ] Git commit en todos los resultados nuevos
- [ ] `verify_packaged_artifact` sin `--skip-install` en CI
- [ ] Batería paper E1–E2 (no ejecutada; fuera de alcance)
