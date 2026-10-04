# NEXO Sprints 31–34 — Fase 4 (deliberación, World2D legacy, LIF, publicación)

## Sprint 31 — Puente deliberación
- **`deliberation_bridge_mode: integrated`**
- `DeliberationBridgeAuditProcess` + eventos `deliberation.bridge`
- Autoridad motora: **integrado** (legacy = advisory)
- Export: `deliberation_bridge_export`

## Sprint 32 — Acciones legacy en World2D
- **`world2d_legacy_actions_mode: integrated`**
- `nexo/demo/world2d_actions.py`: mapeo `tv`→`inspect_distractor`, etc.
- **Tarea `legacy_navigation`**

## Sprint 33 — Sonda escala LIF/GPU
- **`lif_scale_mode: integrated`**
- `nexo/behavioral/lif_scale.py`: disponibilidad GPU + bench opcional (`run_bench: true`)
- No integra LIF en scheduler integrado (honesto)

## Sprint 34 — Bundle publicación
- **`publication_mode: integrated`**
- `nexo/behavioral/publication.py`: manifest + result + config snapshot
- **Manifiesto v8** (9 tareas) | **Perfil máximo**: `integrated_v34.yaml`

## Verificación

```powershell
python -m pytest tests/test_sprints_31_34_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v34.yaml --ticks 18
```

## Roadmap integrado

**Sprints 1–34 completos.**
