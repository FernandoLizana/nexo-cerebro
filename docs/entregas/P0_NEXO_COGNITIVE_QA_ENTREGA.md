# P0 — NEXO Cognitive QA · artefacto de entrega

**Fecha:** 2026-08-18  
**Baseline:** `integrated_v90`  
**Git:** `3a0233c3c4fe504bcad5b545d7bbc43d0e6c2608` · rama `feature/nexo-integrated-brain-v1`  
**Python:** 3.11.0 · Windows-10-10.0.26200

Este archivo es el handoff autosuficiente. Una sesión nueva de Cursor debe poder continuar P1 leyendo **este documento + el repositorio**.

P0 **no construye Cognitive QA**. P0 construye la red de seguridad.

---

## 1. Resumen ejecutivo

NEXO v90 quedó **congelado, ejecutado y documentado**. El núcleo cognitivo no se reescribió. Cognitive QA existe solo como namespace vacío (`nexo_qa`) desactivado.

- Tests freeze: **604 passed / 1 failed / 0 skipped** (605 ejecutados). El fallo es **preexistente** (`test_grounding` distancia a nevera).
- Smoke nexo_qa: **1 passed**.
- Reproducibilidad v90 seed 42, 12 ticks: `trajectory_hash` **idéntico** en dos corridas.
- Comportamiento cognitivo **no modificado**.
- **No** hay Playwright, Selenium, BrowserWorld, personas ni friction score.

**Veredicto:** CONDITIONAL PASS (baseline válido; 1 fallo legado documentado, no introducido por P0).

---

## 2. Estado del repositorio

| Área | Conteo (inventory script) |
|------|---------------------------|
| `brain/` | 128 py |
| `nexo/` | 194 py |
| `tests/` | 93 py (606 collected after nexo_qa) |
| `experiments/` | 246 files / 42 py |
| `configs/` | 79 files |
| `scripts/` | 16 files |

Inventario reutilizado: `python -m scripts.generate_repository_inventory` → `reports/repository_inventory.json` y copia `artifacts/baseline/p0/repository_inventory.json`.

Dependencias: `python -m scripts.check_dependency_consistency` → **OK**. Pillow: `requirements.txt` `<12` vs pyproject `<13` vs lock `12.1.1` (preexistente).

`COMMIT_HASH.txt` / `ENVIRONMENT.json` siguen desactualizados (`NO_GIT_REPOSITORY`). La verdad P0 es git HEAD.

Workspace sucio ajeno a P0: `data/brain_state/*`, `data/library/test-lib_*.txt` — **no** incluidos.

---

## 3. Arquitectura encontrada

Dos bucles reales:

1. **Integrado:** `nexo/integrated_runtime.py` `IntegratedRuntime` → `CognitiveScheduler` → duck type `percepts_for_agent` / `available_actions` / `action_info` / `apply_action`.
2. **Legacy:** `brain/mind.py` `InfantApeBrain.world_tick` → `NeuralAgentLoop` → `World2D.apply_motor`.

v90 `world_mode: world_demo_facade` comparte `brain.world` pero nexo **sigue** ejecutando `apply_action`.

`nexo/environment.py` **no** es el mundo: es snapshot git/plataforma.

Detalle: `docs/cognitive_qa/P0_ARCHITECTURE_MAP.md`, `P0_CURRENT_ENVIRONMENT_CONTRACT.md`.

---

## 4. Baseline de tests

| | |
|--|--|
| Collected (freeze run) | 605 |
| Passed | 604 |
| Failed | 1 |
| Skipped / xfailed / errors | 0 / 0 / 0 |
| Duración | 1666 s (~28 min) |
| nexo_qa import | 1 passed (aparte; collection actual 606) |

Fallo: `tests/test_grounding.py::test_grounding_can_guide_motivated_navigation_without_forcing_choice`  
`after_distance` 345.48 ≮ `before_distance` 344.72.

**P0 no lo corrigió** (regla: no ocultar fallos preexistentes).

CI: subset histórico intacto + paso `Cognitive QA P0 import smoke`.

HEAVY notables: `test_smoke_results` ~267 s; varios sprints 51–58 55–110 s.

---

## 5. Baseline de reproducibilidad

Método: `runtime_from_config(configs/nexo/integrated_v90.yaml)` + `run(ticks=12)`, `NEXO_SKIP_GPU_BENCH=1`, seed 42.

| | Run A | Run B |
|--|-------|-------|
| hash | `77b06e9f…cce1d9c` | igual |
| acciones | 12× `explore` | igual |
| energy | 0.3526710863756767 | igual |
| mean_reward | 0.12 | igual |
| certificates válidos | 12 | 12 |
| agency_score | 1.0 | 1.0 |
| wall time | 3.69 s | 3.44 s |

STRICT: hash/acciones/certs. INFORMATIONAL: tiempo; UUID de episodios (`uuid4` en `RoomWorld.apply_action`).

La trayectoria **todo explore** es comportamiento real del facade v90 en 12 ticks, no un error de P0.

---

## 6. Mapa cognitivo (síntesis)

KEEP: WM, hipocampo, TD, fatiga, afecto, metacognición, certificado causal, agency audit, event log, fingerprint, config.

KEEP_AND_WRAP_LATER: percepción, atención, PFC (`ROOM_ACTION_SCHEMAS`), BG (fallback `rest`), motor, affordances, task registry, world duck type.

SCIENTIFIC_ONLY: replication, FDR, permutation, meta-analysis, paper pipeline.

LEGACY: `InfantApeBrain` tasks, imaginación, memoria semántica brain, Flask demo.

UNKNOWN: symbol cards, hero journey — no borrar.

Tabla completa: `docs/cognitive_qa/P0_COGNITIVE_CAPABILITY_MAP.md`.

---

## 7. Contrato environment / agente

Nombres reales (no inventados):

- `RoomWorld.percepts_for_agent()`
- `RoomWorld.available_actions()`
- `RoomWorld.action_info(action)`
- `RoomWorld.apply_action(action)`
- `MotorExecutionProcess.step` → `apply_action` (priority 55)
- Decisión: `PrefrontalDeliberator.run` + `ActionGate.select` → evento `action.selected`

---

## 8. Acoplamientos al mundo

CRITICAL 9 · HIGH 11 · MEDIUM 6 · LOW 1  
Ver `docs/cognitive_qa/P0_WORLD_COUPLING_AUDIT.md`.

Los más bloqueantes para BrowserWorld: `ROOM_ACTION_SCHEMAS`, `DriveField.action_bias`, factory tipada a `RoomWorld`, remap `drink→rest` / `unknown→explore`, dual motor facade+legacy tick.

P0 **no** desacopló nada.

---

## 9. Riesgos y deuda

Ver `docs/cognitive_qa/P0_RISKS_AND_TECH_DEBT.md` (P0-RISK-001 … 012).

Deuda **nueva de QA:** aún no hay Protocol, ActionSchema, BrowserWorld, flag runtime. Eso es P1+, no fallo de P0.

---

## 10. Archivos creados

### Código mínimo

- `nexo_qa/__init__.py`
- `tests/nexo_qa/__init__.py`
- `tests/nexo_qa/test_p0_import.py`

### Documentación

- `docs/cognitive_qa/PRINCIPLES.md`
- `docs/cognitive_qa/adr/ADR-0001-cognitive-qa-as-extension.md`
- `docs/cognitive_qa/P0_BASELINE.md`
- `docs/cognitive_qa/P0_ARCHITECTURE_MAP.md`
- `docs/cognitive_qa/P0_WORLD_COUPLING_AUDIT.md`
- `docs/cognitive_qa/P0_CURRENT_ENVIRONMENT_CONTRACT.md`
- `docs/cognitive_qa/P0_HARDCODED_ACTIONS_AUDIT.md`
- `docs/cognitive_qa/P0_COGNITIVE_CAPABILITY_MAP.md`
- `docs/cognitive_qa/P0_TEST_BASELINE.md`
- `docs/cognitive_qa/P0_REPRODUCIBILITY_BASELINE.md`
- `docs/cognitive_qa/P0_DEPENDENCY_BASELINE.md`
- `docs/cognitive_qa/P0_V90_CONFIG_BASELINE.md`
- `docs/cognitive_qa/p0/V90_CONFIG_BASELINE.md` (puntero)
- `docs/cognitive_qa/P0_RISKS_AND_TECH_DEBT.md`
- `docs/cognitive_qa/P0_HANDOFF_TO_P1.md`
- `P0_NEXO_COGNITIVE_QA_ENTREGA.md` (este archivo)

### Artefactos machine-readable

- `artifacts/baseline/p0/baseline.json`
- `artifacts/baseline/p0/tests.json`
- `artifacts/baseline/p0/environment.json`
- `artifacts/baseline/p0/dependencies.json`
- `artifacts/baseline/p0/config_snapshot.json`
- `artifacts/baseline/p0/known_failures.json`
- `artifacts/baseline/p0/performance.json`
- `artifacts/baseline/p0/repository_inventory.json`
- `artifacts/baseline/p0/reproducibility/{run_A,run_B,comparison}.json`

---

## 11. Archivos modificados

- `.gitignore` — excepción `artifacts/baseline/p0/`; patrones futuros `.env`, `sessions/`, `credentials/`, etc. **sin borrar** reglas previas.
- `pyproject.toml` — `include` `nexo_qa*`.
- `.github/workflows/tests.yml` — un job extra de import; **no** se reemplazó la CI científica.

**No modificados:** `configs/nexo/integrated_v90.yaml`, procesos cognitivos, certificados, memoria, PFC, reward, sueño.

---

## 12. Evidencia de (no) regresión

P0 no tocó el loop. Además, dos ejecuciones v90 consecutivas coinciden en hash/acciones/energía/certs.

Golden a preservar en P1:

`trajectory_hash = 77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c`

---

## 13. Decisiones tomadas

- Extensión desacoplada (`ADR-0001`), no rewrite.
- Flag `cognitive_qa.enabled` **especificado, no cableado** a `IntegratedRuntimeConfig` (YAML v90 intacto).
- Reutilizar scripts de inventario/deps; no duplicar herramientas.
- No implementar ActionSchema.
- No arreglar `test_grounding` ni marcar skip.

## 14. Decisiones deliberadamente postergadas

- Protocolo World / MockWorld / ActionSchema (P1)
- Un motor por tick (P1)
- BrowserWorld / Playwright (P2+)
- Personas, friction, HFP (fases posteriores)
- Batería v19 full, paper, GPU 50k, roadmap 91/100
- Modernizar dependencias / Pillow bound
- Actualizar `OPEN_ISSUES.md` histórico

---

## 15. Quality gate

| Gate | Resultado |
|------|-----------|
| A Repository | PASS |
| B Testing | CONDITIONAL PASS (1 preexisting fail documented) |
| C Reproducibility | PASS |
| D Architecture | PASS |
| E Scientific preservation | PASS |
| F Cognitive QA skeleton | PASS (no web) |

---

## 16. Definición exacta de P1

Leer `docs/cognitive_qa/P0_HANDOFF_TO_P1.md`.

Alcance máximo:

1. Protocolo typing alrededor del duck type actual, **sin cambiar firmas**.
2. MockWorld en tests.
3. Diseño ActionSchema alimentado por `action_info`, defaulting a verbos actuales para no romper el golden hash.
4. Seguir con QA **disabled**.

Fuera de P1: navegador real, personas, cambiar algoritmos de memoria/sueño/TD/certificado.

---

## Checklist “esta es la versión donde nació Cognitive QA”

- [x] Tests que pasaban: 604 (+ smoke 46 integrado v80/v90 + nexo_qa)
- [x] Tests que fallaban: 1 grounding navigation
- [x] Configuración: `integrated_v90.yaml` seed 42
- [x] Dependencias: lock + consistency OK
- [x] Comportamiento golden: 12× explore, hash arriba
- [x] Interfaz cerebro–mundo: duck type RoomWorld
- [x] Acoplamientos: auditados
- [x] Módulos cognitivos: mapeados
- [x] Preservar vs abstraer: KEEP vs KEEP_AND_WRAP_LATER
- [x] Cognitive QA no alteró NEXO
