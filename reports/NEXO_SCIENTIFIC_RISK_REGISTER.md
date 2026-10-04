# Registro de riesgos científicos — NEXO

**Actualizado:** 2026-08-04

| ID | Riesgo | Evidencia | Mitigación |
|----|--------|-----------|------------|
| R1 | Afirmar consciencia por `enable_consciousness` | `brain/consciousness.py` | Renombrar a "global access funcional"; métricas externas |
| R2 | Métrica circular `legacy_agency` como éxito | smoke experiments históricos | Tareas en `nexo/behavioral_tasks.py`; primarias externas |
| R3 | Módulos decorativos sin dinámica | inventario 267 módulos, muchos no en loop | Auditoría por sprint; estados honestos en trazabilidad |
| R4 | Reglas que garantizan resultado | revisión manual pendiente por módulo | Prohibición explícita; tests metamórficos |
| R5 | Trazabilidad inflada | 91/100 unable_to_verify | `NB-*` roadmap honesto |
| R6 | LLM como decisor | agent_loop reflect phase | LLM solo verbalización (política documentada) |
| R7 | RNG no centralizado | grep `np.random` en brain/ | Migración a RandomStreams |
| R8 | Resultados no reproducibles | sin git commit en runs | Metadatos seed+hash obligatorios |
| R9 | Confundir simulación con biología | nomenclatura neuroanatómica | Lenguaje "proxy computacional" |
| R10 | Sobrecarga computacional | 128 módulos brain | Perfiles unit/smoke/compact; neural_detail=functional |

## Métricas prohibidas como primarias

```text
binding_active, workspace_ignited, pfc_veto, hippocampus_enabled,
dopamine_level, consciousness_flag, legacy_agency (sin tarea externa)
```

## Nivel de evidencia requerido por capacidad

```text
conceptualizada → implementada → unit_tested → integrated
→ experiment_defined → experiment_executed → supported | inconclusive | failed
```
