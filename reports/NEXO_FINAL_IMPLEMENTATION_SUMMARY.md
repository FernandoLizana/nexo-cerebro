# Resumen implementación — NEXO Integrated Brain Sprint 1

**Fecha:** 2026-08-04  
**Rama:** feature/nexo-integrated-brain-v1  
**Tests integrados:** 11/11 passed  
**Tests totales recopilados:** 334 (suite completa no ejecutada)

## Sprint 3 (2026-08-04)

- `nexo/perception/` — jerarquía predictiva, error, precisión, percepción activa
- `nexo/thalamus/` — relay, reticular, context gate
- `nexo/core/process_perception.py` — pipeline predictivo integrado al scheduler
- Config: `configs/nexo/integrated_v3.yaml` (`perception_mode: predictive`)
- Tests: `tests/test_predictive_perception.py` (10 tests)
- Compatibilidad: `perception_mode: legacy` preserva v1/v2

## Sprint 2 (2026-08-04)

- `nexo/body/` — VirtualBody, metabolismo, interocepción, circadiano
- `nexo/homeostasis/` — drives competitivos, alostasis, controlador
- Procesos: `MetabolismProcess`, `BodyInteroceptionProcess`, `AllostasisProcess`
- Config: `configs/nexo/integrated_v2.yaml`
- Tests: `tests/test_body_homeostasis.py` (7 tests)
- Demo v2: energía final ~0.16 a 80 ticks (seed 42), no colapso a 0

## Entregables Sprint 1

- `nexo/core/` — estado, eventos, reloj, scheduler, procesos
- `nexo/connectome/` — grafo, routing, plasticidad acotada
- `nexo/telemetry/` — recorder con niveles
- `nexo/demo/room_scenario.py` — mundo mínimo
- `nexo/integrated_runtime.py` — runtime integrado
- `nexo/run.py` — CLI legacy + integrado
- `configs/connectome/connectome_v1.yaml`
- `configs/nexo/{integrated_v1,legacy,smoke}.yaml`
- `tests/test_integrated_core.py`
- `experiments/integrated_demo/run_recurrent_demo.py`

## Demo ejecutada

```powershell
python -m experiments.integrated_demo.run_recurrent_demo
python -m nexo.run --config configs/nexo/smoke.yaml
```

## Reproducibilidad verificada

- Misma semilla → mismo `trajectory_hash` (test automatizado)
- Semillas distintas → hashes distintos (test automatizado)

## No implementado (Sprints 2–10)

Hipocampo reconstructivo completo, neuromodulación, sueño, social, batería E1–E8, etc.

Ver `reports/NEXO_OPEN_RESEARCH_QUESTIONS.md`.
