# NEXO Cognitive Lab — Plan de Transformación Científica

**Fecha:** 2026-09-06  
**Rama:** `feature/nexo-cognitive-lab`  
**Base:** `c5892c3e` — *Add NEXO Cognitive QA P1-P9…* (anterior al SaaS)  
**Fase en tip:** `nexo_qa.__phase__ = "P9"` · `__version__ = "0.9.0-p9"`  
**Estado de este documento:** PLAN ONLY — **no** implementa P10/P11 ni producto comercial.

---

## Principio fundamental

> **NEXO no afirma simular humanos.**  
> **NEXO estudia agentes sintéticos parametrizados mediante características cognitivas.**

Todo perfil, métrica y taxonomía se trata como **instrumento experimental**.  
NCFS, EHFP, CRS y derivados se etiquetan **`experimental / non-validated`** hasta validación contra datos humanos reales (hoy: `NO_HUMAN_DATA`).

---

## 0. Decisión estratégica

| Decisión | Detalle |
|----------|---------|
| Abandonar SaaS | No billing, usuarios comerciales, planes, créditos, multi-tenancy, portal cliente |
| Conservar ciencia | Rescatar P0–P9 útil; no borrar código científico por defecto |
| Renombrar misión | De “Cognitive QA producto” → **NEXO Cognitive Lab** |
| Tip limpio | Trabajar desde `c5892c3e`; residuales SaaS **untracked** (`nexo_qa/product/`, `data/product.db`, prompts portal) → **REMOVE** en limpieza inmediata |
| Siguiente paso | Este plan → limpieza/archival → ExperimentSpec + Viewer local (sin fases P10/P11 comerciales) |

La rama SaaS (`feature/nexo-integrated-brain-v1` @ `eb6943aa`+) permanece en historial si se necesita referencia; **no** es el camino del laboratorio.

---

## 1. Estado actual (exhaustivo)

### 1.1 Capas del sistema

```text
app.py (:5000)          → laboratorio interactivo / observatory (brain + demos)
brain/                  → agente monolítico neuro-inspirado (InfantApeBrain, loops, memoria SQLite…)
nexo/                   → IntegratedRuntime + procesos (PFC, WM, hipocampo, percepción…)
nexo_qa/                → harness experimental P0–P9 (mundos, perfiles, métricas, población, chaos, human_lab)
configs/nexo_qa/        → contratos YAML versionados
tests/test_p0…p9        → gates de reproducibilidad
docs/cognitive_qa/      → diseño + ADRs 0001–0010
```

**No pertenece al lab (y no debe entrar):**

```text
nexo_qa/product/   portal / créditos / RBAC / API comercial
Landing SaaS       portal cliente premium
P10 entrega/docs   productización comercial
```

### 1.2 Flujo científico ya existente (a preservar)

```text
Experiment config (YAML + seed)
        ↓
PopulationPlanner / ChaosPlanner
        ↓
IntegratedRuntime + bind_world + bind_task + bind_persona
        ↓
MockWorld | BrowserWorld (+ optional chaos wrapper)
        ↓
Trace capture → analysis → metrics → failure certificates
        ↓
Aggregation / paired deltas / reports
```

### 1.3 Hipótesis científica guía (objeto del lab)

> Agentes sintéticos con **distintos perfiles cognitivos parametrizados** producen, ante **las mismas tareas** y **condiciones controladas**, diferencias **consistentes y reproducibles** en:
>
> - estrategias de navegación  
> - tasas de finalización  
> - patrones de fallo (taxonomía P6)  
> - recuperación tras error  
> - sensibilidad a perturbaciones ambientales (P8)

Esto es **ciencia de agentes**, no validación UX humana —hasta que exista protocolo P9 con datos reales.

---

## 2. Clasificación de componentes

Leyenda:

| Clase | Significado |
|-------|-------------|
| **KEEP** | Útil tal cual para el lab; mantener en camino principal |
| **REFACTOR** | Útil, pero renombrar/aclarar claims, disclaimers o API |
| **ARCHIVE** | Conservar fuera del camino crítico (referencia / comparator) |
| **REMOVE** | SaaS, demo tóxico para ciencia, o residual comercial |

### 2.1 `nexo_qa/` — harness P0–P9

| Componente | Path | Clase | Notas |
|------------|------|-------|-------|
| Package markers | `nexo_qa/__init__.py` | **REFACTOR** | Renombrar misión a Cognitive Lab; fase `LAB` o `P9-lab`; docstring honesto |
| MockWorld + WebLab server | `testing/` | **KEEP** | Harness offline + fixtures HTTP |
| Environment bind helpers | `testing/__init__.py` | **KEEP** | API de cableado experimental |
| BrowserWorld + Playwright + policy | `browser/` | **KEEP** | Substrate web controlado; allowlist |
| Action mapper / protocol | `browser/*` | **KEEP** | Contrato ActionSchema |
| Perception hybrid/DOM/salience | `perception/` | **KEEP** | Modelo perceptual **ingenieril**, no visión humana validada |
| Vision stub | `perception/vision.py` | **ARCHIVE** | `NOT_IMPLEMENTED` — no fingir VISION |
| Goals / TaskContext / oracle | `goals/` | **KEEP** | Oracle **test-only**; no al runtime cognitivo |
| Personas (presets + mapping) | `personas/` | **REFACTOR** | → *Synthetic Cognitive Profiles*; no “humanos” |
| Persona YAMLs | `configs/nexo_qa/personas/` | **REFACTOR** | Relabel `profiles/` o disclaimer fuerte |
| Analysis / traces | `analysis/` | **KEEP** | Backbone de reproducibilidad |
| Failure taxonomy + certificates | `failures/` | **KEEP** | Taxonomía de fallos de **agentes**; mejorar labels |
| Metrics NCFS/EHFP/CRS | `metrics/` | **REFACTOR** | Marcar `experimental / non-validated`; considerar prefijo `sim_` / `lab_` |
| EHFP naming | `metrics/ehfp.py` | **REFACTOR** | No es probabilidad humana; proxy de simulación |
| Population engine | `population/` | **KEEP** | Corazón del Experimental Engine |
| Seeds / planner / runner / state | `population/*` | **KEEP** | Reproducibilidad multi-run |
| Stress / clustering | `population/stress.py`, `clustering.py` | **KEEP** | Clustering = exploratorio |
| Population CLI | `population/cli.py` | **KEEP** | Entrypoint lab |
| Chaos paired design | `chaos/` | **KEEP** | Condiciones controladas + deltas |
| Human lab stack | `human_lab/` | **REFACTOR** | Framework futuro; default `NO_HUMAN_DATA`; no claims HFP |
| Synthetic fixtures | `human_lab/synthetic.py` | **KEEP** | Solo tests de pipeline |
| Calibration gates OOD | `human_lab/calibration/` | **KEEP** | Honestidad científica — conservar |
| Reporting JSON/MD | `reporting/` | **KEEP** | Artefactos de lab |
| Scenarios / oracle | `scenarios/` | **KEEP** | Expandir tareas experimentales |
| **Product / portal / SaaS** | `nexo_qa/product/` | **REMOVE** | Residual untracked o commits posteriores — fuera del lab |

### 2.2 `nexo/` — runtime integrado

| Componente | Clase | Notas |
|------------|-------|-------|
| `IntegratedRuntime` + config | **REFACTOR** | Congelar *ExperimentSpec* slim (pocos modos) |
| Scheduler / StateStore / events | **KEEP** | Contrato de experimento |
| ActionSchema / EnvironmentProtocol | **KEEP** | Si viven en `nexo/core` o equivalentes |
| PFC + executive + BG | **KEEP** | Política de selección del agente |
| Working memory + hippocampus | **KEEP** | Knobs de perfil |
| Perception processes | **KEEP** | Preferible a stack vision monolítico de `brain/` |
| Body / neuromod / TD | **KEEP** (opcional) | Covariables controladas (fatiga, arousal) |
| Connectome / lesions | **KEEP** | Diseños de ablación |
| Telemetry / RandomStreams / trajectory hash | **KEEP** | Reproducibilidad |
| `*_mode` sprawl (~muchas flags) | **REFACTOR** | Reducir a perfiles de experimento tipados |
| LegacyBrainAdapter / dual PFC | **REFACTOR → ARCHIVE** | Un solo executive owner por corrida primaria |
| `nexo.demo.*` (flask, day-in-life, companion) | **ARCHIVE** | No son API científica |
| Behavioral paper pipelines | **ARCHIVE** | Offline; no runtime |
| Social ToM / language | **ARCHIVE** | Solo si hay protocolo social explícito |

### 2.3 `brain/` — monolito histórico

| Componente | Clase | Notas |
|------------|-------|-------|
| Algoritmos reutilizables (deliberation, WM, hippo ideas) | **REFACTOR** | Cantera de algoritmos / comparator |
| `InfantApeBrain` monolito | **ARCHIVE** (para EE) | Demasiados side-systems para control experimental |
| Curricula / clinical / symbol cards / companion / youtube | **REMOVE** del camino EE | Contaminan ActionSchema y RNG |
| Vascular / gustation / ragdoll / food | **ARCHIVE** | Embodiment ≠ control |
| `data/brain_state` persistente | **REFACTOR** | Estado no efímero → riesgo de leak entre “runs frescos” |

### 2.4 UI / scripts / docs / tests

| Componente | Clase | Notas |
|------------|-------|-------|
| `app.py` + templates lab | **REFACTOR** | Viewer/inspector local; no producto |
| Tests `test_p0`…`test_p9` | **KEEP** | Gates científicos |
| Tests / scripts / docs P10 + portal | **REMOVE** | SaaS |
| `scripts/generate_p5…p9_artifacts.py` | **KEEP** | Evidencia regenerable |
| Entregas `P0`…`P9_*.md` | **ARCHIVE** | Historia de fase; no borrar |
| Docs `docs/cognitive_qa/P0–P9` + ADR-0001…0010 | **KEEP** | Canon científico |
| Docs P10 / product / ADR-0011 | **ARCHIVE/REMOVE** | Fuera del lab |
| Configs personas/poblaciones/chaos/failures/metrics | **KEEP** (+ REFACTOR naming perfiles) |
| `PROMPT_PORTAL_*`, master SaaS artifact | **ARCHIVE** | Histórico comercial |

---

## 3. Qué rescatar de P0–P9 (mapa → Cognitive Lab)

| Fase | Rescate para el Lab | Reencuadre |
|------|---------------------|------------|
| **P0** | Baseline, safety net, no tocar core a ciegas | Freeze científico |
| **P1** | EnvironmentProtocol, ActionSchema, MockWorld | Mundos controlados |
| **P2** | BrowserWorld, policy, Web Lab | Entornos web experimentales |
| **P3** | Percepción híbrida limitada | Percepts sintéticos (no “ojos humanos”) |
| **P4** | Goals, TaskContext, oracle separado | Tareas reproducibles |
| **P5** | Trait→parameter map, presets | **Synthetic Cognitive Profiles** |
| **P6** | Taxonomía, certificates, NCFS/EHFP/CRS | Fallos + métricas **experimental** |
| **P7** | Population, seeds, stress, aggregation | Experimental Engine multi-agente |
| **P8** | Paired chaos, deltas | Experimental Conditions |
| **P9** | Dataset schemas, OOD gates, HBC framework | Preparación futura; **sin claims** hoy |

**No rescatar como objetivo:** productización, créditos, RBAC comercial, portal cliente, marketing de “QA cognitivo SaaS”.

---

## 4. Arquitectura objetivo — NEXO Cognitive Lab

```text
┌─────────────────────────────────────────────────────────────┐
│                 Experiment Viewer (local)                   │
│  seleccionar: experimento · perfiles · condiciones · N     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                  Experimental Engine                         │
│  ExperimentSpec → plan → run → checkpoint → aggregate        │
│  (refactor de population/ + chaos/ runners)                  │
└───────┬─────────────────────┬───────────────────┬───────────┘
        │                     │                   │
        ▼                     ▼                   ▼
 Synthetic Cognitive    Controlled          Experimental
 Profiles (P5)          Environments        Conditions (P8+)
 metódico,              MockWorld           baseline, latency,
 impaciente,            BrowserWorld        visual interference,
 distraído,             Web Lab fixtures    delayed feedback,
 explorador…            (sitios controlados errors, WM pressure,
                        futuros)            UI mutations
        │                     │                   │
        └────────────┬────────┴─────────┬─────────┘
                     ▼                  ▼
              IntegratedRuntime    Measurements
              (nexo slim)          completion, actions,
                                   duration, loops,
                                   backtracking, errors,
                                   recovery, paths,
                                   variability
                     │
                     ▼
              Failure Taxonomy (P6)
                     │
                     ▼
              Datasets (JSONL/CSV) + Reproducibility Bundle
              (seed, config hash, code version, env, conditions)
                     │
                     ▼
              Statistical Analysis (comparar poblaciones/condiciones
                                   sin inventar conclusiones)
```

### 4.1 Experimental Engine

- Entrada: `ExperimentSpec` (YAML/JSON) inmutable por corrida  
- Salida: run records + aggregates + provenance  
- Reutilizar: `PopulationPlanner`, `PopulationRunner`, `ChaosPlanner`, seeds, state/resume  
- Prohibido: credits, orgs, API keys, tenants

### 4.2 Synthetic Cognitive Profiles

Renombrar conceptualmente (y luego en código) **personas → profiles**:

| Profile (lab) | Origen probable P5 | Parámetros (ejemplo) |
|---------------|--------------------|----------------------|
| Metódico / baseline | `baseline` | WM media, baja impulsividad |
| Impaciente | `impatient` | paciencia↓, impulsividad↑ |
| Distraído | `high_distractibility` | atención dispersa |
| Explorador | (nuevo o mix) | novelty / exploración↑ |
| Baja WM | `low_wm` | capacidad WM↓ |
| Cansado | `fatigued` | fatiga↑ |
| Precavido | `risk_averse` | riesgo↓ |
| Novato digital | `novice_digital` | literacidad digital↓ |

**Disclaimer obligatorio en configs y reportes:**  
*Perfil sintético parametrizado — no representa un ser humano real.*

### 4.3 Controlled Environments

1. **MockWorld** (determinista, CI)  
2. **Web Lab / BrowserWorld** (fixtures HTML locales)  
3. **Futuro:** sitios experimentales controlados (allowlist estricta; sin scanner abierto)

### 4.4 Experimental Conditions

Mapear P8 + extensiones:

| Condición | Fuente |
|-----------|--------|
| Baseline | P7/P8 BASELINE |
| Latencia | P8 LATENCY |
| Interferencias visuales | P8 VISUAL / layout |
| Feedback tardío | P8 FEEDBACK_DELAY |
| Errores transitorios | P8 TRANSIENT_ERROR |
| Presión de memoria | tareas P5/P7 + perfiles low_wm |
| Mutaciones de UI | P8 visual + fixtures chaos |
| Interrupciones / modales / sesión | P8 |

Diseño preferido: **pareado** (mismo seed × perfil × tarea; baseline vs condition).

### 4.5 Measurements

| Medida | Estado |
|--------|--------|
| Completion rate | KEEP / reportar |
| Nº de acciones | KEEP |
| Duración | KEEP |
| Loops / backtracking | KEEP (goals/progress + taxonomy) |
| Errores / recuperación | KEEP (P6) |
| Rutas recorridas | KEEP / enriquecer path dumps |
| Variabilidad inter-seed | KEEP (P7 distributions) |
| **NCFS** | **experimental / non-validated** |
| **EHFP** | **experimental / non-validated** (proxy sim; ≠ HFP humano) |
| **CRS** | **experimental / non-validated** |
| **HFP** | **bloqueado** hasta datos humanos + dominio calibrado |

### 4.6 Failure Taxonomy

- Conservar P6 taxonomy + certificates  
- Mejorar labels orientados a agentes (no diagnóstico)  
- Versionar (`failures-v1` → v2 solo con migración documentada)

### 4.7 Experiment Reproducibility

Cada corrida debe registrar al menos:

```text
experiment_id, run_id, master_seed, child_seed
profile_id + profile_hash
environment_id + fixture/version
condition_id + perturbation_spec_hash
task_id + task_version + goal hash
code_version / git commit
nexo_qa version / metrics_version / taxonomy_version
config snapshot (YAML frozen)
RNG policy (RandomStreams owner)
backend (mock | browser)
timestamp UTC
```

### 4.8 Datasets

- Preferir **JSONL** por run + **CSV** agregados  
- Separar: raw traces (refs) vs summaries  
- Layout sugerido:

```text
datasets/lab/<experiment_id>/
  experiment_spec.json
  runs.jsonl
  aggregates.csv
  provenance.json
```

### 4.9 Statistical Analysis

- Reutilizar aggregation P7 + paired deltas P8  
- Añadir utilidades: CI bootstrap, effect sizes, tablas población×condición  
- **Prohibido:** conclusiones causales inventadas; reports deben listar limitaciones

### 4.10 Experiment Viewer

UI **local sencilla** (Flask o CLI+HTML mínimo):

- Selección: experimento, población/perfiles, condiciones, N runs  
- Lanzar / ver progreso / tablas / plots simples  
- **No** login comercial, **no** multi-tenant  
- Puede nacer refactorizando `app.py` *o* un `scripts/lab_viewer.py` delgado sobre runners existentes

---

## 5. Hipótesis científicas posibles (ejemplos falsables)

1. **H1 — Perfil × completion:** Bajo las mismas tareas Web Lab, perfiles `impatient` y `high_distractibility` muestran completion rate menor que `baseline` (Δ ≥ umbral pre-registrado).  
2. **H2 — Chaos sensitivity:** Ante `FEEDBACK_DELAY`, el incremento de NCFS (proxy) y la caída de completion son mayores en `impatient` que en `baseline` (diseño pareado).  
3. **H3 — Failure signatures:** La distribución de familias P6 (`DISTRACTOR_CAPTURE` vs `NAVIGATION_LOOP`) difiere significativamente entre `novice_digital` y `expert_digital`.  
4. **H4 — WM pressure:** Tareas de alta demanda de memoria aumentan `WORKING_MEMORY_LOSS` más en `low_wm` que en `baseline`.  
5. **H5 — Path diversity:** Entropía de rutas / backtracking es mayor en perfiles exploratorios que en metódicos, a completion comparable.

Todas requieren: pre-registro de N, seeds, métricas primarias, y **no** extrapolar a humanos.

---

## 6. Deuda técnica (bloqueadores de ciencia limpia)

| Riesgo | Impacto | Mitigación en Lab |
|--------|---------|-------------------|
| Dual executive (`brain` vs `nexo` PFC) | Misma seed ≠ misma política | EE primario **sin** LegacyBrainAdapter |
| Explosión de `*_mode` flags | Combinatoria opaca | ExperimentSpec slim tipado |
| RNG no centralizado en `brain/` | Contaminación de trajectory | Un dueño de RNG por corrida |
| Memoria dual (SQLite vs in-memory) | Episodios no comparables | Path único documentado por experimento |
| Vocabulario demo en acciones | Confunde tareas | Action allowlist por experimento |
| `data/brain_state` persistente | Leak entre sesiones | Directorios efímeros / limpieza |
| Métricas con nombres “humanos” | Overclaim | Disclaimers + rename gradual |
| P9 sin datos humanos | Tentación de HFP | Gates OOD existentes — reforzar en UI lab |
| Residuales SaaS untracked | Contaminan imports | **REMOVE** `nexo_qa/product/`, `data/product.db` |
| Playwright opcional | CI frágil | Mock por defecto; browser marcado |

Baseline documentado v90 `trajectory_hash`:  
`77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c` — preservar como regresión del core cuando el EE toque `nexo/`.

---

## 7. Plan de trabajo (sin P10/P11 comerciales)

### Fase L0 — Alineación (inmediata)

1. Confirmar tip `c5892c3e` en `feature/nexo-cognitive-lab`  
2. Eliminar residuales SaaS untracked (`nexo_qa/product/`, portal artifacts, `data/product.db`)  
3. Archivar (no borrar git history) entregas/docs comerciales si reaparecen  
4. Publicar este plan + disclaimer global en README lab

### Fase L1 — Rebrand científico

1. Renombrar conceptualmente personas → profiles (código + configs + docs)  
2. Marcar NCFS/EHFP/CRS como `experimental / non-validated` en registry y reportes  
3. Actualizar `nexo_qa/__init__.py` (misión Lab)  
4. Tests verdes P0–P9

### Fase L2 — ExperimentSpec + Datasets

1. Definir schema `ExperimentSpec` + provenance bundle  
2. Export JSONL/CSV estándar  
3. Unificar entrypoints CLI (`nexo-lab run|aggregate|export`)

### Fase L3 — Experiment Viewer local

1. UI mínima: elegir spec, N, perfiles, condiciones, ver tablas  
2. Sin auth comercial

### Fase L4 — Análisis estadístico

1. Tablas población×condición, CIs, effect sizes  
2. Plantillas de reporte con limitaciones obligatorias

### Fase L5 — (Futuro, no ahora) Human validation

1. Solo cuando existan datos reales bajo protocolo P9  
2. Entonces — y solo entonces — discutir HFP calibrado

**Explícitamente fuera de alcance ahora:** billing, tenants, portal SaaS, P10 producto, claims de simulación humana.

---

## 8. Criterios de éxito del laboratorio (Definition of Coherent Lab)

El proyecto se considera **laboratorio coherente** cuando:

```text
[ ] Tip limpio sin capa SaaS en el árbol de trabajo
[ ] Principio “no simula humanos” visible en docs y reportes
[ ] Profiles sintéticos documentados + disclaimers
[ ] Engine ejecuta experimentos reproducibles (seed → artefacto)
[ ] Condiciones baseline vs chaos pareadas disponibles
[ ] Measurements + taxonomy P6 exportables JSONL/CSV
[ ] NCFS/EHFP/CRS marcados experimental/non-validated
[ ] HFP no aparece como claim
[ ] Tests P0–P9 PASS
[ ] Viewer local puede lanzar y mostrar un experimento demo
[ ] Ningún path de créditos/RBAC/portal en el flujo científico
```

---

## 9. Resumen ejecutivo

| Pregunta | Respuesta |
|----------|-----------|
| ¿Se abandona SaaS? | **Sí** |
| ¿Se parte de pre-SaaS? | **Sí — `c5892c3e` / rama `feature/nexo-cognitive-lab`** |
| ¿Se tira P0–P9? | **No** — se rescata y reencuadra |
| ¿Se implementan P10/P11 ahora? | **No** |
| ¿Qué se escribe primero? | **Este plan** |
| ¿Afirma NEXO simular humanos? | **No** |
| ¿Qué estudia? | Agentes sintéticos parametrizados y sus diferencias conductuales |

---

## 10. Próxima acción recomendada (tras aprobar este plan)

1. Limpieza REMOVE de residuales SaaS untracked  
2. Commit de este archivo en `feature/nexo-cognitive-lab`  
3. Ejecutar **L1** (rebrand + disclaimers métricas) sin tocar el core cognitivo  
4. Luego **L2** ExperimentSpec + datasets  

---

*Documento vivo. Actualizar cuando cambie la clasificación KEEP/REFACTOR/ARCHIVE/REMOVE o se complete una fase L0–L4.*
