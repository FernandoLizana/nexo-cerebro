# NEXO Sprint 6 — Aprendizaje integrado

## Alcance implementado

- **Neuromodulación (`nexo/neuromodulation/`)**: DA, 5-HT, NE, ACh, GABA, glutamato; actualización por recompensa, estrés, novedad y atención.
- **RL TD (`nexo/reinforcement/`)**: tabla V(s,a), error δ, sesgos Go acotados (≤0.10) inyectados en ganglios basales.
- **Plasticidad conectómica**: `PlasticityState.update()` activado en aristas clave tras |δ| saliente.
- **Procesos (`nexo/core/process_learning.py`)**:
  - `TDBiasProcess` (prioridad 61, antes de BG)
  - `NeuromodulatorUpdateProcess` (54, post-motor)
  - `TDLearningProcess` (53, post-motor)
  - `ConnectomePlasticityProcess` (52, post-motor)
- **Runtime**: `learning_mode: legacy | integrated` y perfil `configs/nexo/integrated_v6.yaml`.

## Pipeline aprendizaje (modo integrated)

```text
… → TDBias (sesgo Go) → BG → motor → reward → neuromod → TD update → plasticidad
```

## Eventos nuevos

| Evento | Rol |
|--------|-----|
| `td.bias_computed` | Sesgos Go para BG |
| `td.updated` | δ y actualización V(s,a) |
| `neuromodulation.updated` | Snapshot moduladores |
| `plasticity.updated` | Cambios en aristas plásticas |

## Verificación

```powershell
python -m pytest tests/test_learning_integrated.py tests/test_executive_integrated.py tests/test_memory_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v6.yaml
```

## Limitaciones honestas

- TD sobre estado tabular coarse (drive + energy bucket), no embeddings.
- Plasticidad Hebbiana escalar por arista, sin STDP ni BCM.
- Sin replay de sueño ni metaplasticidad lifecycle.
- Sesgo TD acotado; PFC/deliberación sigue siendo soberana.

## Próximo sprint sugerido

Sprint 7: workspace global y metacognición.
