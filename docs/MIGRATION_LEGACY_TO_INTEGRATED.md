# Migración legacy → integrado v1

## Ejecución

```powershell
# Legacy (InfantApeBrain histórico)
python -m nexo.run --config configs/nexo/legacy.yaml --legacy

# Integrado v1 (scheduler recurrente)
python -m nexo.run --config configs/nexo/integrated_v1.yaml

# Smoke CI
python -m nexo.run --config configs/nexo/smoke.yaml
```

## Diferencias conductuales esperadas

| Aspecto | Legacy | Integrado v1 |
|---------|--------|--------------|
| Orquestación | Cadena fija agent_loop | Scheduler multiescala |
| Estado | Atributos brain dispersos | StateStore + eventos |
| Mundo demo | World2D completo | RoomWorld mínimo (Sprint 1) |
| Semillas | RandomStreams | RandomStreams (mismo sistema) |
| Decisión | PrefrontalDeliberation | BasalGangliaSelector competitivo |

## Regresión

Los tests legacy en `tests/` no se eliminan. Sprint 1 añade `tests/test_integrated_core.py`.

## Próximos sprints

Roadmap integrado Sprints 1–58 completado. Perfil máximo: `configs/nexo/integrated_v58.yaml`.

## Paridad legacy (Fase 9)

| Aspecto | Legacy | Integrado v54+ |
|---------|--------|----------------|
| Adapter brain | Antes de deliberación fija | `LegacyEarlyBrainAdapterProcess` priority 61 |
| World2D headless | `brain/world.py` completo | `World2DHeadlessWorld` facade (step_toward) |
| Roadmap100 | Flags en InfantApeBrain | `roadmap100_bridge_mode` + auditoría advisory |

## Demo integrado (Fase 10)

| Aspecto | Legacy Flask | Integrado v58 |
|---------|--------------|---------------|
| UI demo | `app.py` + InfantApeBrain | Bridge advisory + batería |
| Vista 3D | `game3d.js` sobre world 2D | `world3d_sync_mode` exporta mismo esquema |
| Autonomía | API 403 en rutas motoras | `autonomy_guard_mode` + auditoría |
| Nira | `brain/companion.py` | `companion_integrated_mode` dyad advisory |

Modos Fase 10: `flask_demo_bridge_mode`, `world3d_sync_mode`, `autonomy_guard_mode`, `hypothalamus_multimodal_mode`, `companion_integrated_mode`.

## Flask unificado (Fase 11–12)

```powershell
python app.py
# Legacy puro (desactivar unificación):
$env:NEXO_FLASK_LEGACY="1"; python app.py
```

- `FlaskUnifiedSession`: motor legacy o **integrado primario** (`unified_motor_mode`)
- `WorldDemoFacade`: mismo `brain.world` en runtime integrado
- Modos: `flask_unified_mode`, `unified_motor_mode`

## Cognición y memoria (Fase 13)

| Aspecto | Antes (v66) | Integrado v70 |
|---------|-------------|---------------|
| Post-tick Flask | Solo sync deliberación/cuerpo | `agent_loop_sync_mode` — think + persona + companion |
| Memoria | SQLite legacy ≠ HippocampalStore | `memory_bridge_mode` — paridad advisory |
| Rutas estudio | Legacy directo | `flask_study_proxy_mode` — overlay integrado |
| Condiciones E | Solo bridge flags | `roadmap100_e_block_mode` — auditoría E1–E8 |

Perfil máximo: `configs/nexo/integrated_v70.yaml`. Batería: `integrated_v17.yaml`.

## Organismo auditable (Fase 14)

| Aspecto | Antes (v70) | Integrado v80 |
|---------|-------------|---------------|
| Memoria post-sueño | Bridge advisory (conteos) | `memory_unification_mode` — promoción hippo→SQLite tras consolidación |
| Agency | Deliberación + motor unificado | `causal_certificate_mode` — certificado causal por tick |
| Fenomenología | Event log disperso | `day_in_the_life_mode` — timeline 24h acelerada (288×300s) |

Perfil máximo: `configs/nexo/integrated_v80.yaml`. Batería: `integrated_v18.yaml`. Flask demo: `flask_unified_v4.yaml`.

## Ciencia reproducible (Fase 15)

| Aspecto | Integrado v90 |
|---------|---------------|
| Agency | `agency_audit_mode` — score + certificados v2 post-motor |
| Ciencia personal | `science_bundle_mode` — envelope H1+H2 + scripts reproduce |
| Certificado | `causal_certificate` v2 — `agency_valid`, `reward_value` |

Perfil máximo: `configs/nexo/integrated_v90.yaml`. Batería: `integrated_v19.yaml`.
