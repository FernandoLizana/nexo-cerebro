# NEXO Sprints 51–54 — Fase 9 (paridad legacy)

## Sprint 51 — Legacy adapter temprano
- **`legacy_adapter_early_mode: integrated`**
- `LegacyEarlyBrainAdapterProcess` priority **61** (antes de BG integrado)
- Export: `legacy_adapter_early/integrated_v54_timing.json`
- Tarea: `legacy_adapter_timing`

## Sprint 52 — World2D headless
- **`world2d_headless_mode: integrated`** + `world_mode: world2d_headless`
- `World2DHeadlessWorld`: `step_toward`, proximidad mobiliario
- Tarea: `world2d_headless_navigation`

## Sprint 53 — Puente roadmap100
- **`roadmap100_bridge_mode: integrated`**
- Flags `roadmap100_full_v1` en `InfantApeBrain` + auditoría advisory
- Export: `roadmap100_bridge/integrated_v54_bridge.json`
- Tarea: `roadmap100_bridge_smoke`

## Sprint 54 — Perfil v54 + batería v13
- **Perfil máximo**: `integrated_v54.yaml` · batería v13 (16 tareas)
- CI smoke: v54 + manifest v13 mini

## Verificación

```powershell
python -m pytest tests/test_sprints_51_54_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v54.yaml --ticks 12
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v13_mini.yaml
```

## Limitaciones honestas

- World2D headless ≠ `brain/world.py` headless completo (facade integrado)
- Roadmap100 bridge es **advisory** vía flags; no replica stacks legacy en scheduler
- Adapter temprano mejora timing vs priority 40 pero no garantiza paridad bit-a-bit

## Roadmap integrado

**Sprints 1–54 completos.** Fase 10 (Flask/3D/autonomía) → ver Sprints 55–58.
