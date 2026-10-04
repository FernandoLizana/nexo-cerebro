# NEXO Sprints 39–42 — Fase 6 (motor unificado, env legacy, battery paper, publicación completa)

## Sprint 39 — Deliberación unificada motora
- **`deliberation_unified_mode: integrated`**
- `DeliberationUnifiedProcess` → `action.unified` actualiza `current_action` antes del cerebelo
- Política: **`integrated_wins`** con autoridad motora `unified`
- **Tarea `deliberation_conflict_resolution`**

## Sprint 40 — Entorno legacy enriquecido
- **`world2d_legacy_env_mode: integrated`**
- `World2DLegacyEnvWorld`: mobiliario, habitaciones, `env_fidelity_score`
- **`world_mode: world2d_legacy_env`**
- **Tarea `world2d_legacy_env_navigation`**

## Sprint 41 — Battery paper pipeline
- **`battery_paper_mode: integrated`**
- `export_battery_paper()`: CSV + LaTeX desde reportes de batería
- Integrado en `full_publication` y pipeline

## Sprint 42 — Publicación completa
- **`full_publication_mode: integrated`**
- Bundle: publicación + paper_pack + battery_paper
- **Manifiesto v10** (12 tareas) | **Perfil máximo**: `integrated_v42.yaml`

## Verificación

```powershell
python -m pytest tests/test_sprints_39_42_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v42.yaml --ticks 18
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v10_mini.yaml
```

## Roadmap integrado

**Sprints 1–42 completos.**

## Limitaciones (honestas)

- Entorno legacy enriquecido ≠ simulación completa `brain/world.py` headless
- Deliberación unificada usa legacy de ticks previos (legacy adapter priority 40)
- Battery paper requiere reportes JSON existentes en `results/integrated_battery/`
