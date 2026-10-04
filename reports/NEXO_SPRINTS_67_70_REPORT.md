# NEXO Sprints 67–70 — Fase 13

**Perfil:** `integrated_v70`  
**Batería:** v17 (28 tareas) / v17_mini (4 tareas CI)  
**Flask demo:** `flask_unified_v3.yaml` (default session)

## Sprints

| Sprint | Entrega | Flag |
|--------|---------|------|
| 67 | `agent_loop_sync_mode` — post-tick cognitivo lite (think, persona, companion) | `agent_loop_sync_mode: integrated` |
| 68 | `memory_bridge_mode` — paridad advisory SQLite ↔ HippocampalStore | `memory_bridge_mode: integrated` |
| 69 | `flask_study_proxy_mode` — overlay en rutas `/api/*/study` | `flask_study_proxy_mode: integrated` |
| 70 | `roadmap100_e_block_mode` — auditoría condiciones E1–E8 | `roadmap100_e_block_mode: integrated` |

## Verificación

```powershell
python -m pytest tests/test_sprints_67_70_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v70.yaml --ticks 12
python app.py
```

## Limitaciones (honestas)

- `agent_loop_sync` es **lite**: no re-ejecuta perceive/commit/act/learn del loop completo
- `memory_bridge` compara conteos; **no** fusiona almacenes SQLite e integrado
- Rutas estudio siguen ejecutando lógica legacy; el proxy solo añade metadata integrada
- E-block audita resolución de condiciones, no corre baterías E1–E8 completas
