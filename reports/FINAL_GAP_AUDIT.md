# Auditoría final de brechas — NEXO reproducibilidad

**Generado:** 2026-08-04T17:10:00+00:00  
**Python:** 3.11.0  
**Git commit:** `NO_GIT_REPOSITORY` (sin repositorio git inicializado)  
**Inventario detallado:** `reports/repository_inventory.json`

---

## Comandos de inventario ejecutados

```powershell
python --version                    # 3.11.0
git rev-parse HEAD                  # fatal: not a git repository
git status --porcelain              # fatal: not a git repository
python -m pytest --collect-only -q  # 323 tests collected (post norecursedirs)
python scripts/generate_repository_inventory.py
```

---

## Estado por directorio

| Directorio | Existe | Archivos | Python | Notas |
|------------|--------|----------|--------|-------|
| `brain/` | Sí | 128 | 128 | Núcleo cognitivo; incluido en ZIP |
| `nexo/` | Sí | 12 | 12 | Reproducibilidad, configs, auditoría |
| `experiments/` | Sí | 235 | 32 | Scripts; `results/` excluido del ZIP |
| `scripts/` | Sí | 15 | 12 | build, verify, traceability |
| `tests/` | Sí | 60 | 60 | 323 tests recopilados |
| `configs/` | Sí | 5 | 0 | YAML experimentales |
| `schemas/` | Sí | 1 | 0 | `experiment_result.schema.json` |
| `reports/` | Sí | 15+ | 0 | Reportes de verificación |
| `docs/` | Sí | 16 | 0 | Documentación reproducibilidad |
| `roadmap/` | Sí | 1 | 0 | `roadmap100_traceability.json` |
| `.github/` | Sí | 1 | 0 | `workflows/tests.yml` |
| `data/` | Sí | parcial | 0 | `curriculum/` incluido; `brain_state/` excluido |

---

## Brechas identificadas en entrega anterior vs estado actual

| # | Problema reportado | Estado |
|---|-------------------|--------|
| 1 | ZIP sin `brain/` | **Corregido** — prefijo `brain/` presente (128 módulos) |
| 2 | ZIP sin `experiments/` | **Corregido** — prefijo `experiments/` presente |
| 3 | Archivos declarados inexistentes | **Parcial** — entregables de reproducibilidad creados; git ausente |
| 4 | `verify_artifact` falla antes del reporte | **Corregido** — imports diferidos + `finally` v2.1.0 |
| 5 | `pass` no correspondía al paquete extraído | **Corregido** — `verify_packaged_artifact` scope separado |
| 6 | ZIP vacío en algunas rutas | **Corregido** — validación previa/posterior; falla explícita |
| 7 | Rutas personales y `__pycache__` | **Corregido** — exclusiones por nombre; escaneo contenido |
| 8 | Trazabilidad 100 genérica | **Corregido** — 91× `unable_to_verify`; 9 con evidencia real |
| 9 | Ablaciones desde baseline | **Corregido** — ablaciones v1 desde `roadmap100_full_v1` |
| 10 | Tareas externas con vars internas | **Parcial** — `nexo/behavioral_tasks.py` con métricas primarias externas |
| 11 | Tests RNG débiles | **Corregido** — `tests/test_reproducibility.py` ampliado |
| 12 | Auditoría aprueba sin `brain/` | **Corregido** — `audit_fail` si no hay archivos |
| 13 | `ExperimentResult` no integrado | **Corregido** — 5 JSON en `results/smoke/` |
| 14 | Lock incompatible con pyproject | **Corregido** — `check_dependency_consistency` OK |
| 15 | Sin verificar ZIP extraído | **Corregido** — `verify_packaged_artifact` status `pass` |

---

## Rutas personales detectadas (workspace)

Muestras en inventario (no incluidas en ZIP público):

- `experiments/results/_battery_smoke_e12/battery_smoke_report.json`
- `reports/SNAPSHOT_PRE_REFACTOR.json`, `ENVIRONMENT.json`
- Scripts de empaquetado (definen marcadores; excluidos del escaneo ZIP)

`KNOWN_LIMITATIONS.md` redactado para eliminar rutas absolutas del paquete.

---

## Archivos obligatorios del artefacto

Todos presentes en `dist/NEXO_REPRODUCIBLE_0.3.0.zip` según `dist/artifact_manifest.json`:

- Prefijos: `brain/`, `nexo/`, `experiments/`, `tests/`, `data/curriculum/`
- Metadatos: `pyproject.toml`, `requirements*.txt`, `CITATION.cff`, `LICENSE`, `CHANGELOG.md`

---

## Problemas abiertos (no bloqueantes de empaquetado)

1. Sin repositorio git → `commit=NO_GIT_REPOSITORY` en resultados
2. Suite completa 323 tests no ejecutada en CI local (subconjunto 30 OK)
3. Trazabilidad: 91/100 sin evidencia mapeable (honesto, no inventado)
4. RNG legacy residual en algunos módulos (`memory_store`, `regions`)
5. Batería E1–E8 no ejecutada (fuera de alcance)
6. `verify_packaged_artifact --skip-install` usado en verificación final (pip install pendiente en CI)

---

## Referencias

- `reports/packaged_artifact_verification.json` — status `pass`
- `reports/artifact_verification.json` — scope `workspace_verification`, status `pass`
- `dist/artifact_manifest.json` — SHA256 y conteo de archivos
