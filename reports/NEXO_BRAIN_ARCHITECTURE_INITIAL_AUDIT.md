# Auditoría arquitectónica inicial — NEXO Brain Integration

**Rama:** `feature/nexo-integrated-brain-v1`  
**Fecha:** 2026-08-04  
**Python:** 3.11.0  
**Git:** repositorio inicializado; sin commits aún (`HEAD` no disponible)  
**Módulos inventariados:** 267  
**Aristas de dependencia:** 355  

---

## 1. Arquitectura actual (pre-integración)

NEXO/cerebro es un **sistema modular legacy** centrado en `brain/mind.py` (`InfantApeBrain`) y `brain/agent_loop.py` (`NeuralAgentLoop`).

### Flujo dominante legacy

```text
world_tick() → agent_loop.run()
  → interocept → perceive → cognize → [imagine] → commit
  → verify → act → learn → reflect
```

- **128 módulos Python** en `brain/` con nombres neuroanatómicos heterogéneos.
- **Infraestructura reproducibilidad** en `nexo/` (semillas, condiciones, auditoría decisiones).
- **Roadmap 100:** flags en `brain/experiment_flags.py`; ablaciones en `nexo/experiment_conditions.py`.
- **Experiments E1–E8:** scripts en `experiments/`; resultados parciales en `experiments/results/`.

### Hallazgos críticos

| ID | Hallazgo | Severidad |
|----|----------|-----------|
| A1 | Orquestación monolítica vía `agent_loop` secuencial | Alta |
| A2 | ~90+ módulos brain con integración desigual | Alta |
| A3 | Métricas internas (`agency`, `binding_active`) usadas históricamente como proxy conductual | Media |
| A4 | RNG parcialmente centralizado (`nexo/random_streams`); residuo legacy | Media |
| A5 | `SimulationClock` existente pero no cableado en todo el loop | Media |
| A6 | Connectome blueprint escala lógica 86B, no grafo funcional operacional | Media |
| A7 | Documentación histórica afirma capacidades no respaldadas experimentalmente | Alta |
| A8 | Trazabilidad Roadmap 100: 91/100 `unable_to_verify` | Info |

---

## 2. Comandos baseline ejecutados

```powershell
python --version                          # 3.11.0
git rev-parse HEAD                        # ERROR: sin commits
git status --porcelain                    # untracked masivo (init reciente)
python -m pytest --collect-only -q tests/ # 334 tests
python scripts/generate_nexo_brain_audit.py # 267 módulos, 355 edges
python -m pytest tests/test_integrated_core.py -q  # 11 passed
```

Suite completa 334 tests: **no ejecutada** en esta sesión (tiempo).

---

## 3. Sprint 1 implementado en esta rama

Nueva capa `nexo/core/` + `nexo/connectome/` + `nexo/integrated_runtime.py`:

- Estado cognitivo tipado (`CognitiveState`, `HomeostaticState`, `AffectiveState`)
- Eventos inmutables + `StateStore` reducer
- `SimulationClock` simulado (sin `time.time()`)
- `CognitiveScheduler` multiescala
- Conectoma YAML v1 (`configs/connectome/connectome_v1.yaml`)
- Demo recurrente (`nexo/demo/room_scenario.py`)
- CLI: `python -m nexo.run --config configs/nexo/integrated_v1.yaml`

---

## 4. Compatibilidad legacy

- `python -m nexo.run --config configs/nexo/legacy.yaml --legacy` → `InfantApeBrain`
- `LegacyBrainAdapterProcess` disponible (opcional, period 5)
- Sin modificaciones destructivas a `brain/agent_loop.py` en Sprint 1

---

## Referencias

- `reports/NEXO_MODULE_INVENTORY.json`
- `reports/NEXO_DEPENDENCY_GRAPH.json`
- `reports/NEXO_CURRENT_DATAFLOW.md`
- `reports/NEXO_SCIENTIFIC_RISK_REGISTER.md`
- `docs/MIGRATION_LEGACY_TO_INTEGRATED.md`
