# Auditoría inicial del repositorio NEXO/cerebro

**Fecha:** 2026-08-04  
**Snapshot:** ver `ENVIRONMENT.json`, `COMMIT_HASH.txt`, `reports/SNAPSHOT_PRE_REFACTOR.json`  
**Python:** 3.11.0  
**OS:** Windows 10 (win32 10.0.26200)  
**Git:** **NO** — `fatal: not a git repository`  
**Estado dirty/clean:** N/A (sin git)

---

## Resumen ejecutivo

| Aspecto | Hallazgo |
|---------|----------|
| Tests recopilados (post-fix) | **308** (`pytest --collect-only`) |
| Tests recopilados (pre-fix) | 292 + **17 errores de colección** |
| Causa colección rota | Duplicados `tests/` en `artifacts/` y `publication_finalization/` |
| Repositorio git | Ausente |
| pyproject.toml | Ausente → **creado** en refactor |
| Semillas centralizadas | Ausentes → **implementadas** (`nexo.random_streams`) |
| Condición `full` ambigua | Era `AblationFlags()` sin roadmap → **documentado** como `baseline` |

---

## 1. Errores de importación

| Severidad | Descripción | Evidencia |
|-----------|-------------|-----------|
| Resuelto | Duplicados de módulos test por `artifacts/**/tests` | `reports/_pytest_collect.txt` líneas 309–427 |
| Menor | `pyyaml` no listado en `requirements.txt` original | requerido por configs YAML |

No se detectaron módulos `brain.*` faltantes en importación directa.

---

## 2. Errores de ejecución

| Severidad | Ubicación | Descripción |
|-----------|-----------|-------------|
| **Crítico (corregido)** | `brain/episodic_context.py:162` | `ValueError` shapes (128,) vs (384,) en `multimodal_similarity` durante `world_tick` headless |
| Conocido | `brain/deliberation.py:408` (pre-fix) | RNG recreado desde `age_ticks` → no reproducible por semilla |

---

## 3. Tests fallidos (pre-refactor)

Ejecución parcial documentada:

- `tests/test_reproducibility.py` — **2 failed** antes del fix episodic_context (crash en recall)
- Subconjunto post-fix: **7 passed** en 162s (`test_reproducibility.py`)
- Subconjunto configs+stats+validation: **20 passed, 2 failed** (reproducibility)

Suite completa: ver `reports/pytest-output.txt` (ejecución en curso al cierre de Fase 0).

---

## 4. Tests no recopilados

17 archivos en `tests/` no se recopilaban por **import file mismatch** con copias en:

- `artifacts/nexo_entrega_20260804/tests/`
- `publication_finalization/relevant_source/tests/`

**Mitigación:** `pyproject.toml` → `norecursedirs`.

---

## 5. Dependencias faltantes / incompletas

| Paquete | Estado |
|---------|--------|
| flask, numpy, scipy, pillow, pypdf | En `requirements.txt` |
| pyyaml | Faltaba → añadido vía `pyproject.toml` |
| pytest | Dev dependency |
| cupy | Opcional GPU (`requirements-gpu.txt`) |

---

## 6. Problemas de reproducibilidad

1. **Sin git commit** en metadatos experimentales.
2. **RNG desde `age_ticks`** en deliberación e imaginación.
3. **`np.random.seed(seed)` global** en `run_batch.make_brain` sin flujos independientes.
4. **Rutas absolutas** en resultados: `experiments/results/_battery_smoke_e12/battery_smoke_report.json` → `C:\Users\<USER>\...`
5. **Condición `full`** no activaba roadmap100 — ambigüedad metodológica grave.

---

## 7. Problemas metodológicos

| ID | Problema |
|----|----------|
| M1 | Documentación afirmaba "libre albedrío" / "61 passed" sin distinguir unit vs integración |
| M2 | Batería nombrada "E1–E8 @10k" pero E4–E8 usan perfil `compact` |
| M3 | Métrica `spike_aligned=0` bajo `nobind` presentada como efecto conductual |
| M4 | Resultados E1 GPU: desviación estándar 0 en CSV (semillas idénticas en métricas agregadas) |
| M5 | Roadmap marcado "completado" sin trazabilidad por ítem |

---

## 8. Problemas documentales

- `docs/ARTEFACTO_ROADMAP_100_NEXO.md` — rutas `C:\Users\<USER>\...`
- README principal no describe instalación editable ni verificación única
- Cifra "61 passed" no coincide con recolección real (308 tests)

---

## 9. Problemas científicos

- Claims de agency/libre albedrío sin calificación de proxy computacional
- Sin esquema de metadatos en CSV/JSONL históricos
- Sin hash de configuración en resultados legacy

---

## 10. Deuda técnica

- Duplicación masiva: `publication_finalization/`, `artifacts/`, `pack_gpt_adaptive_behavior/`
- ~154 módulos `brain/*.py` sin empaquetado formal previo
- RNG disperso en `memory_store`, `regions`, `archetype_cards`, `subcortex`
- Dominio demo incrustado en `ACTION_SCHEMAS` (`clinical`, `biopsych`)

---

## 11. Riesgos de publicación

1. Revisor externo no puede reproducir sin git hash
2. Afirmaciones de libre albedrío/consciencia
3. Métricas circulares bajo ablaciones
4. Batería paper incompleta presentada como avance completo

---

## Inventario de módulos (muestra)

| Área | Cantidad aprox. | Notas |
|------|-----------------|-------|
| `brain/*.py` | 154 | Núcleo cognitivo |
| `experiments/*.py` | 28 | Runners E1–E8, batería |
| `tests/*.py` | ~60 | Sin duplicados artifacts |
| `configs/` | 0 → creado | Post-auditoría |

---

## Scripts experimentales identificados

- `experiments/run_batch.py` — E1/E2 headless
- `experiments/run_battery_10k.py` — orquestador legacy
- `experiments/run_sleep.py`, `run_e4_*`, `run_e5_*`, `run_e7_*`, `run_arena_*`
- `experiments/bench_tick_gpu.py`

---

## Acciones iniciadas en refactor (post-auditoría)

Ver `reports/IMPLEMENTATION_SUMMARY.md`.
