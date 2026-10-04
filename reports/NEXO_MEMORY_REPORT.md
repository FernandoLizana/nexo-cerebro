# NEXO Sprint 4 — Memoria integrada

## Alcance implementado

- **Memoria de trabajo (`nexo/working_memory/`)**: buffer con capacidad limitada, decaimiento temporal, interferencia entre ítems similares y refuerzo reciente.
- **Hipocampo (`nexo/memory/hipocampus/`)**: episodios reconstructivos con *pattern separation* en codificación y *pattern completion* imperfecta en recuperación.
- **Procesos (`nexo/core/process_memory.py`)**:
  - `EnhancedWorkingMemoryProcess` — sustituye WM legacy cuando `memory_mode: integrated`
  - `HippocampalRetrievalProcess` — recuperación antes de selección de acción (prioridad 62)
  - `HippocampalEncoderProcess` — codificación tras recompensas salientes
- **Runtime**: `memory_mode: legacy | integrated` en `IntegratedRuntimeConfig` y perfil `configs/nexo/integrated_v4.yaml`.
- **Ganglios basales**: sesgo de acciones por episodios recuperados (`retrieved_episodes` en config del scheduler).
- **Telemetría de resultado**: `hippocampal_episodes`, `memory_encodings`, `memory_retrievals`.

## Modos

| Modo | Pipeline memoria |
|------|------------------|
| `legacy` | `WorkingMemoryProcess` simple (Sprint 1) |
| `integrated` | WM mejorada → recuperación hipocampal → codificación → BG con sesgo mnésico |

## Reproducibilidad

- RNG de memoria aislado vía `RandomStreams.memory` (`memory_rng` en config del scheduler).
- Misma semilla + perfil v4 → mismo `trajectory_hash` y conteos mnésicos.

## Verificación

```powershell
python -m pytest tests/test_memory_integrated.py tests/test_integrated_core.py tests/test_body_homeostasis.py tests/test_predictive_perception.py -q
python -m nexo.run --config configs/nexo/integrated_v4.yaml
```

## Limitaciones honestas (no declaradas como completadas)

- Sin consolidación lenta sueño/transferencia a neocórtex.
- Sin olvido activo ni replay offline.
- Recuperación usa cue heurístico desde percepción reciente, no consulta explícita del usuario.
- `world.episodes` (legacy demo) y `HippocampalStore` coexisten; no están unificados.

## Próximo sprint sugerido

Sprint 5: PFC, ganglios basales completos, cerebelo y planificación multi-paso.
