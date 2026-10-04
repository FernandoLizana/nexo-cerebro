# NEXO Sprint 10 — Batería conductual y ablaciones

## Alcance implementado

- **Métricas (`nexo/behavioral/`)**: supervivencia, entropía de acciones, ratios eat/distractor/rest, recompensa media.
- **Tareas integradas**: `survival`, `distractor_control`, `reproducibility`.
- **Ablaciones (`nexo/ablation/`)**: 8 perfiles que desactivan capas o procesos (`abl_no_memory`, `abl_no_pfc`, etc.).
- **Evaluación en runtime**: `BehavioralSnapshotProcess` emite `behavior.snapshot` cada 20 ticks.
- **Runner**: `experiments/integrated_battery/run_battery.py`
- **Configs**: `configs/nexo/integrated_v10.yaml`, `configs/battery/integrated_v1.yaml`

## Modo evaluación

```yaml
evaluation_mode: integrated  # legacy | integrated
```

## Ablaciones disponibles

| ID | Efecto |
|----|--------|
| `integrated_full` | Stack completo |
| `abl_no_memory` | `memory_mode: legacy` |
| `abl_no_executive` | `executive_mode: legacy` |
| `abl_no_learning` | `learning_mode: legacy` |
| `abl_no_consciousness` | `consciousness_mode: legacy` |
| `abl_no_social` | `social_mode: legacy` |
| `abl_no_sleep` | `sleep_mode: legacy` |
| `abl_no_pfc` | deshabilita `prefrontal_deliberation` |

## Verificación

```powershell
python -m pytest tests/test_behavioral_integrated.py -q
python -m experiments.integrated_battery.run_battery --seeds 42 --ablations integrated_full abl_no_pfc
python -m nexo.run --config configs/nexo/integrated_v10.yaml
```

## Limitaciones honestas

- Tareas acotadas a RoomWorld (6 acciones), no batería legacy completa.
- Ablaciones por modo/proceso, no lesiones connectome fine-grained.
- Métricas conductuales proxy, no validación clínica.

## Roadmap integrado — completo (Sprints 1–10)

Perfil máximo: `integrated_v10` con todas las capas + evaluación.
