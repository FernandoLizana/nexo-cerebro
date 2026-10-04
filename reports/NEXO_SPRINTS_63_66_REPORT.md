# NEXO Sprints 63–66 — Fase 12

## Sprint 63 — WorldDemoFacade
- `world_mode: world_demo_facade` — alias directo de `brain.world`
- Tarea: `world_demo_facade`

## Sprint 64 — Motor único
- **`unified_motor_mode: integrated`**
- `UnifiedMotorProcess` + tick integrado primario en Flask
- Tarea: `unified_motor_smoke`

## Sprint 65 — Flask unificado por defecto
- `NEXO_FLASK_UNIFIED=1` por defecto (`NEXO_FLASK_LEGACY=1` para desactivar)
- Rutas: `/api/state`, `/api/language`, `/api/time` enriquecidas
- Config demo: `flask_unified_v2.yaml`

## Sprint 66 — Perfil v66 + batería v16
- Perfil: `integrated_v66.yaml` (24 tareas)
- Git tag: `integrated_v66`

## Activación

```powershell
python app.py
# o legacy puro:
$env:NEXO_FLASK_LEGACY="1"; python app.py
```

## Limitaciones

- Motor integrado no ejecuta `agent_loop` completo (sin lenguaje/afecto rico por tick)
- Rutas `/api/*` de estudio/curriculum siguen en legacy directo
- Memoria SQLite legacy ≠ HippocampalStore integrado
