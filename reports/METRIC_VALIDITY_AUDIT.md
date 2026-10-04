# Auditoría de validez de métricas

**Fecha:** 2026-08-04

## Resumen

| Métrica | Estado | Riesgo principal |
|---------|--------|------------------|
| `agency` / `legacy_agency_score` | legacy + experimental | Circular con inhibición (+0.2) |
| `confidence` | experimental | Reformulada vía margen (Fase 7) |
| `spike_aligned` | mechanistic | Cero por definición si `nobind` |
| `remembered_rate` | experimental | Alta saturación (~0.995) |
| `surprise` | experimental | Saturación en 1.0 reportada E1 |
| `drive_coherent` | experimental | Heurística 0/0.5/1 |
| `pfc_veto_rate` | mechanistic | Acoplado a binding |
| `inhibited_rate` | mechanistic | Binaria por tick |

---

## legacy_agency_score (antes `agency`)

**Definición:** `clip(winner.pfc / (winner.limbic + winner.pfc + 0.15), 0, 1)`; +0.2 si `inhibited`.

**Código:** `brain/deliberation.py` (~424–426)

**Rango:** [0, 1]

**Interpretación:** Proxy de contribución PFC relativa al ganador; **no** libre albedrío.

**Saturación:** Común en ~0.15 con inhibición boost.

**Flags:** Afectada por `force_limbic_winner`, `disable_affect`.

**Circularidad:** Parcial — inhibición incrementa agency.

**Prueba:** `tests/test_reproducibility.py`, `tests/test_intention_circuit.py`

**Etiqueta:** `legacy`

---

## confidence / confidence_from_margin

**Definición (nueva):** `sigmoid(margin / temperature)` con margen entre top-2 `net`.

**Código:** `nexo/agency_metrics.py`, `brain/deliberation.py`

**Rango:** [0.12, 0.96] tras clip

**Interpretación:** Certeza relativa entre candidatos.

**Casos borde:** <2 candidatos → margen = net del único.

**Etiqueta:** `experimental`

---

## spike_aligned

**Definición:** Alineación spike PFC–decisión (`intention_circuit`).

**Código:** `brain/intention.py`, `experiments/metrics.py`

**Rango:** [0, 1]

**Dependencia flags:** Requiere `bind_deliberation=True`

**Circularidad:** **Alta** bajo `nobind` — métrica mecanística, no conductual primaria.

**Prueba conductual alternativa:** `nexo.behavioral_tasks.task_binding_external`

**Etiqueta:** `mechanistic` / secondary bajo ablaciones

---

## remembered_rate

**Definición:** Fracción de ticks con recall episódico exitoso.

**Código:** `experiments/metrics.py` ← `cognition`/hippo

**Saturación:** ~0.995 en E1 GPU (20 seeds idénticos)

**Advertencia:** Desviación 0 cross-seed requiere inspección de trayectoria (`nexo.statistics`)

**Etiqueta:** `experimental`

---

## surprise

**Definición:** Error de predicción cognitiva por tick.

**Saturación:** 1.0 constante en CSV E1 full documentado.

**Etiqueta:** `experimental` — posible techo numérico

---

## drive_coherent

**Definición:** 1 si acción alineada con drive top; 0.5 si curiosidad; else 0.

**Código:** `experiments/metrics.py:47`

**Unidad:** adimensional

**Etiqueta:** `experimental`

---

## Métricas compuestas nuevas (Fase 7)

Ver `nexo/agency_metrics.py`: `decision_margin`, `top_down_contribution`, `impulse_override_rate`, `action_entropy`, etc.

**Etiqueta:** `experimental`

---

## Recomendaciones

1. Reportar mecanísticas y conductuales por separado en batería paper.
2. Emitir warnings automáticos (`nexo.statistics`) ante constantes cross-seed.
3. No usar `spike_aligned` como primaria en `nobind`.
