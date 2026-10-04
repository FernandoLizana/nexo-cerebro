# NEXO Sprint 5 — Ejecutivo integrado

## Alcance implementado

- **PFC (`nexo/prefrontal/`)**: deliberación límbica vs ejecutiva con veto bajo baja energía.
- **Ganglios basales (`nexo/basal_ganglia/`)**: Go/No-Go, trazas de hábito, integración con deliberación y memoria.
- **Cerebelo (`nexo/cerebellum/`)**: suavizado temporal de acciones antes del motor.
- **Planificación (`nexo/planning/`)**: pila de sub-objetivos para `eat` y `flee` multi-paso en RoomWorld.
- **Procesos (`nexo/core/process_executive.py`)**:
  - `GoalStackProcess` (prioridad 71)
  - `PrefrontalDeliberationProcess` (prioridad 63)
  - `EnhancedBasalGangliaProcess` (prioridad 60)
  - `CerebellarCorrectionProcess` (prioridad 56)
- **Runtime**: `executive_mode: legacy | integrated` y perfil `configs/nexo/integrated_v5.yaml`.

## Pipeline ejecutivo (modo integrated)

```text
GoalStack → WM + hipocampo → PFC deliberation → BG integrado → cerebelo → motor
```

## Eventos nuevos

| Evento | Rol |
|--------|-----|
| `deliberation.completed` | Resultado PFC/límbico |
| `plan.updated` | Plan activo y profundidad |
| `plan.step_advanced` | Avance multi-paso |
| `action.vetoed` | Veto PFC registrado |
| `action.corrected` | Corrección cerebelar |

## Verificación

```powershell
python -m pytest tests/test_executive_integrated.py tests/test_memory_integrated.py tests/test_predictive_perception.py tests/test_integrated_core.py -q
python -m nexo.run --config configs/nexo/integrated_v5.yaml
```

## Limitaciones honestas

- Esquemas de acción limitados a RoomWorld (6 acciones), no port completo de `ACTION_SCHEMAS` legacy.
- Planificación de 2 pasos (`flee`: explore → flee); sin torre completa.
- Cerebelo suaviza por consenso reciente, no modelo forward/inverse.
- Sin neuromodulación dopaminérgica explícita (Sprint 6).

## Próximo sprint sugerido

Sprint 6: plasticidad sináptica, RL y neuromodulación.
