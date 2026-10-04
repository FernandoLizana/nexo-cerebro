# NEXO Sprints 23–26 — Fase 2 (legacy, mundo, inferencia, pipeline)

## Sprint 23 — Puente legacy
- **`legacy_bridge_mode: integrated`**
- `nexo/behavioral/legacy_bridge.py`: compara trayectoria integrada vs `InfantApeBrain` headless
- Export: `legacy_bridge_export` (CLI `--legacy-bridge-output` o `legacy_bridge.auto_export: true`)

## Sprint 24 — Mundo extendido
- **`world_mode: extended`**
- `nexo/demo/extended_room.py`: clima, refugio, acción `seek_shelter`
- **Tarea `foraging`**: métricas `shelter_ratio`, `foraging_score`

## Sprint 25 — Inferencia bootstrap
- **`inference_mode: integrated`**
- `nexo/behavioral/inference.py`: CI bootstrap sobre `mean_delta` en efectos
- Manifiesto: `inference_mode: integrated` en export de estadísticas

## Sprint 26 — Orquestación pipeline
- **`orchestration_mode: integrated`**
- `nexo/behavioral/orchestration.py`: batería + meta-análisis + cross-batería en un paso
- CLI: `--pipeline-manifest configs/battery/integrated_v6_mini.yaml`
- **Manifiesto v6**: 7 tareas | **Perfil máximo**: `integrated_v26.yaml`

## Verificación

```powershell
python -m pytest tests/test_sprints_23_26_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v26.yaml --ticks 30
python -m nexo.run --config configs/nexo/integrated_v26.yaml --legacy-bridge-output results/legacy_bridge/test.json --ticks 8
```

## Roadmap integrado

**Sprints 1–26 completos.** Perfil acumulado: `integrated_v26`.
