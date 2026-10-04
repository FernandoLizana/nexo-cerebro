# Limitaciones conocidas — NEXO

**Actualizado:** 2026-08-04

## Metodológicas

1. **Agency / “libre albedrío”:** las métricas de agencia son *proxies computacionales* de selección centralizada PFC–límbico, no evidencia de libre albedrío fenomenológico ni consciencia.
2. **`spike_aligned` con `nobind`:** puede ser 0 por definición del mecanismo de binding; no usar como métrica conductual primaria bajo esa ablación (ver tareas en `nexo/behavioral_tasks.py`).
3. **`full` legacy ≠ roadmap100:** la condición E1 `full` mapea a `baseline` (dinámicas roadmap OFF). Usar `roadmap100_full` para activar las 100 mejoras.
4. **Batería paper incompleta:** resultados GPU parciales en `experiments/results/battery_10k_gpu/`; no existe `battery_full_report.json` completo.
5. **Significancia estadística:** muestras pequeñas (20 seeds) requieren interpretación cautelosa; `nexo.statistics` emite advertencias, no pruebas de hipótesis formales.

## Técnicas

1. **Sin repositorio git** en el entorno de desarrollo actual → `commit=NO_GIT_REPOSITORY` hasta inicializar git.
2. **Rutas absolutas históricas** en algunos JSON de resultados; nuevos scripts usan `pathlib` vía `nexo.paths`.
3. **Aleatoriedad residual:** módulos legacy (`memory_store`, `regions`, `archetype_cards`) aún usan RNG no centralizado; migración parcial.
4. **GPU:** CuPy opcional; PFC/mundo permanecen en CPU.
5. **Auditoría de decisiones:** AST+regex no cubre `setattr` dinámico (documentado en `nexo/decision_audit.py`).

## Evidencia por mejora roadmap

Tener código + test unitario **no** implica validación científica. Ver `docs/ROADMAP100_TRACEABILITY.md` estados: `implemented` ≠ `supported`.

## Dominio demo

Esquemas de acción incluyen contenido de demo (`clinical`, `biopsych`, `infant`). Separación planificada en adaptadores de escenario (`brain/scenarios/` — pendiente extracción completa).

## Aprendizaje / hábitos

`legacy_reinforce_on_selection: true` en `configs/model/default.yaml` conserva refuerzo histórico por selección; configuración moderna debe usar outcome/reward cuando esté cableado.
