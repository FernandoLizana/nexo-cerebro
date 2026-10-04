# NEXO Sprints 55–58 — Fase 10 (Flask/3D/autonomía/Nira)

## Sprint 55 — Puente Flask demo
- **`flask_demo_bridge_mode: integrated`**
- `FlaskDemoBridgeProcess` + payload compatible con rutas demo
- Export: `flask_bridge/integrated_v58_bridge.json`
- Tarea: `flask_demo_smoke`

## Sprint 56 — Sincronización World3D
- **`world3d_sync_mode: integrated`** + `world_mode: world3d_sync`
- `World3DSyncWorld`: esquema `game3d.js` desde `brain.world.World2D`
- Tarea: `world3d_state_sync`

## Sprint 57 — Contrato de autonomía
- **`autonomy_guard_mode: integrated`**
- Auditoría rutas 403 en `app.py` + eventos `autonomy.guard`
- Export: `autonomy_audit/integrated_v58_audit.json`
- Tarea: `autonomy_contract_audit`

## Sprint 58 — Hipotálamo multimodal + Nira
- **`hypothalamus_multimodal_mode: integrated`**
- **`companion_integrated_mode: integrated`**
- Dyad advisory Nira + fusión señales hacia neuromoduladores
- Tareas: `hypothalamus_multimodal_smoke`, `companion_dyad_smoke`
- **Perfil máximo**: `integrated_v58.yaml` · batería v14 (21 tareas)

## Verificación

```powershell
python -m pytest tests/test_sprints_55_58_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v58.yaml --ticks 12
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v14_mini.yaml
```

## Limitaciones honestas

- 3D sigue siendo **vista Three.js** sobre sim 2D; no motor 3D completo
- Flask demo (`app.py`) sigue usando `InfantApeBrain` directo; el bridge es **advisory** en runtime integrado
- Nira integrada es estado advisory; no reemplaza `brain/companion.py` en demo legacy

## Roadmap integrado

**Sprints 1–58 completos.**
