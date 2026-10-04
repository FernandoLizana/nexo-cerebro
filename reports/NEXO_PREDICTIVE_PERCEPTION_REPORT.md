# Percepción predictiva — Sprint 3

**Fecha:** 2026-08-04  
**Perfil:** `integrated_v3` (`perception_mode: predictive`)

## Pipeline

```text
raw_sensory_capture → thalamic_relay (reticular + context gate)
    → predictive_hierarchy (error + posterior)
    → attention (bottom-up PE + top-down goals)
    → working_memory → basal_ganglia → motor
```

## Módulos

| Ruta | Función |
|------|---------|
| `nexo/perception/hierarchy.py` | 3 niveles: sensory → features → scene |
| `nexo/perception/prediction_error.py` | Error ponderado, sorpresa |
| `nexo/perception/precision_weighting.py` | Precisión atencional |
| `nexo/perception/active_perception.py` | Muestreo orientado por error |
| `nexo/thalamus/relay.py` | Relay con competencia |
| `nexo/thalamus/reticular.py` | Inhibición selectiva / habituación |
| `nexo/thalamus/context_gate.py` | Gating contextual (metas, sueño, estrés) |

## Eventos nuevos

- `thalamus.relayed`
- `perception.prediction_error` (surprise, precision, error vector)

## Compatibilidad

- `perception_mode: legacy` conserva `SensoryRelayProcess` + `AttentionProcess` originales
- v1/v2 sin cambios de comportamiento por defecto

## Tests

`tests/test_predictive_perception.py` — 10 tests

## Limitaciones

- No inferencia Bayesiana exacta
- Embeddings 3D del RoomWorld, no visión real
- Mediodorsal aproximado vía `ContextGate` únicamente
