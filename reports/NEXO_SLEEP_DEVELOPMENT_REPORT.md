# NEXO Sprint 9 — Sueño, consolidación y desarrollo

## Alcance implementado

- **Sueño (`nexo/sleep/`)**: fases `awake → nrem_light → nrem_deep → rem` según presión homeostática + fatiga + circadiano.
- **Consolidación (`nexo/memory/consolidation.py`)**: refuerzo de confianza episódica en NREM profundo + plasticidad hipocampo→PFC.
- **Replay (`HippocampalStore.sample_for_replay`)**: muestreo de episodios durante sueño.
- **Desarrollo (`nexo/development/`)**: etapas `infant → juvenile → mature` por consolidaciones acumuladas.
- **Procesos (`nexo/core/process_sleep.py`)**:
  - `SleepArchitectureProcess` (76)
  - `MemoryReplayProcess` (48)
  - `ConsolidationProcess` (47)
  - `DevelopmentProcess` (46)
- **Runtime**: `sleep_mode: legacy | integrated` y perfil `configs/nexo/integrated_v9.yaml`.

## Pipeline sueño (modo integrated)

```text
SleepArchitecture → … → motor → MemoryReplay → Consolidation → Development
```

Durante sueño, BG sesga fuertemente hacia `rest`.

## Eventos nuevos

| Evento | Rol |
|--------|-----|
| `sleep.phase_changed` | Transición de fase |
| `memory.replayed` | Replay hipocampal |
| `memory.consolidated` | Consolidación NREM profundo |
| `development.updated` | Etapa de maduración |

## Verificación

```powershell
python -m pytest tests/test_sleep_integrated.py tests/test_social_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v9.yaml
```

## Limitaciones honestas

- Arquitectura de sueño simplificada (no spindles/SWR completos).
- Consolidación simbólica, sin transferencia a red cortical densa.
- Desarrollo por contadores, no neurogénesis estructural.
- Requiere presión de sueño acumulada para activar fases (120 ticks en v9).

## Próximo sprint sugerido

Sprint 10: batería conductual y ablaciones sistemáticas.
