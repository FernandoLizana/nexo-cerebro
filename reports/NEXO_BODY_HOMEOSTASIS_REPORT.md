# Cuerpo y homeostasis — Sprint 2

**Fecha:** 2026-08-04  
**Rama:** feature/nexo-integrated-brain-v1

## Implementado

| Módulo | Función |
|--------|---------|
| `nexo/body/body_state.py` | `VirtualBody`, `ActionCost` |
| `nexo/body/metabolism.py` | Drenaje basal calibrado, costos por acción |
| `nexo/body/interoception.py` | Percepción corporal con ruido/sesgo |
| `nexo/body/circadian.py` | Modulación circadiana sobre metabolismo |
| `nexo/homeostasis/drives.py` | Drives competitivos emergentes |
| `nexo/homeostasis/allostasis.py` | Metas anticipatorias |
| `nexo/core/process_body.py` | Procesos metabolism, interoception, allostasis |

## Calibración energética

- Drenaje basal: **0.0006**/tick (antes 0.002 implícito)
- Energía inicial: **0.72**
- A 80 ticks con seed 42: energía final **> 0.08** (test automatizado)

## Integración scheduler

```text
metabolism (1) → interoception (2) → allostasis (10)
→ sensory → attention → WM → BG (usa drives) → motor (aplica MetabolismEngine)
```

## Limitaciones

- Sin modelo de dolor lesionado ni desarrollo
- Circadiano acoplado a tiempo simulado, no a luz ambiental del RoomWorld
- Propriocepción no implementada

## Tests

`tests/test_body_homeostasis.py` — 7 tests
