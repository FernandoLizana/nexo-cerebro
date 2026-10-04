# NEXO Sprints 27–30 — Fase 3 (legacy, World2D, escala, inferencia jerárquica)

## Sprint 27 — Adaptador legacy en runtime
- **`legacy_adapter_mode: integrated`**: instancia `InfantApeBrain` + `LegacyBrainAdapterProcess`
- `nexo/behavioral/legacy_adapter.py`: telemetría legacy vs integrado
- Export: `legacy_adapter_export` (`legacy_adapter.auto_export: true`)

## Sprint 28 — World2D lite
- **`world_mode: world2d_lite`**
- `nexo/demo/world2d_lite.py`: facade sobre `brain.world.World2D`
- **Tarea `navigation_2d`**: `distance_traveled`, `navigation_score`

## Sprint 29 — Perfil de escala
- **`scale_mode: integrated`**
- `nexo/behavioral/scale_profile.py`: eventos/tick, procesos, conectoma, ticks/s
- Export automático: `scale.export_path`

## Sprint 30 — Inferencia jerárquica
- **`hierarchical_inference_mode: integrated`**
- `nexo/behavioral/hierarchical_inference.py`: efectos agrupados por capa de ablación
- **Manifiesto v7**: 8 tareas | **Perfil máximo**: `integrated_v30.yaml`

## Modos nuevos

```yaml
legacy_adapter_mode: integrated
world_mode: world2d_lite    # room | extended | world2d_lite
scale_mode: integrated
hierarchical_inference_mode: integrated
```

## Verificación

```powershell
python -m pytest tests/test_sprints_27_30_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v30.yaml --ticks 20
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v7.yaml
```

## Limitaciones honestas

- World2D lite no porta el entorno legacy completo (1200+ líneas).
- Adaptador legacy corre en paralelo al BG integrado; no fusiona deliberación.
- Escala mide runtime Python, no neuronas LIF GPU.
- Inferencia jerárquica es descriptiva por capa, no modelo bayesiano completo.

## Roadmap integrado

**Sprints 1–30 completos.** Perfil acumulado: `integrated_v30`.
