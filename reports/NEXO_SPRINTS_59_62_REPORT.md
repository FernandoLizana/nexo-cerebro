# NEXO Sprint 59–62 — Fase 11 (Flask unificado)

## Sprint 59 — Sesión unificada
- `FlaskUnifiedSession`: legacy conduce demo, integrado audita en sidecar
- `NEXO_FLASK_UNIFIED=1` activa en `app.py`
- Config demo: `configs/nexo/flask_unified_v1.yaml`

## Sprint 60 — Sidecar sin doble tick
- `run_sidecar()` + `suppress_legacy_world_tick` en adapters legacy
- `bind_legacy_world()` comparte `brain.world` con facade integrada

## Sprint 61 — Rutas Flask
- `/api/world`, `/api/world/tick` enriquecidos con bloque `integrated`
- `/api/integrated/status` nuevo
- `/api/neural/causal/hud` overlay integrado
- `/api/health` indica `flask_unified`

## Sprint 62 — Perfil v62 + batería v15
- **`flask_unified_mode: integrated`**
- Perfil: `integrated_v62.yaml` · batería v15 (22 tareas)
- Tarea: `flask_unified_e2e`

## Activación demo

```powershell
$env:NEXO_FLASK_UNIFIED="1"
python app.py
```

## Verificación

```powershell
python -m pytest tests/test_flask_unified_integrated.py -q
python -m pytest tests/test_sprints_55_58_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v62.yaml --ticks 12
```

## Limitaciones

- Legacy sigue ejecutando `world_tick`; integrado no reemplaza `agent_loop` completo
- Sidecar es auditoría + telemetría; no unifica aún todas las rutas `/api/*`
- Activación unificada es opt-in vía env var
