# ARTEFACTO TÉCNICO — Nexo / cerebro
## Briefing para brainstorming de un “nuevo nivel” del proyecto

> **Uso:** pegar este documento en ChatGPT (o similar) y pedir ideas de arquitectura, experimentos, UX o escala.  
> **Regla:** todo lo numérico y modular aquí debe tratarse como **estado verificado del repo** (julio 2026). Si algo no está en este doc, **no inventarlo** como ya implementado.  
> **No es un paper CLEI.** El paper/publicación está aparcado; el objetivo ahora es **evolución del sistema**.

---

## 0. Meta del briefing

Necesitamos propuestas para un **siguiente nivel** de Nexo que:

1. Respeten la tesis de **libre albedrío / agency**: la deliberación PFC elige `choice_key`; nada (LLM, TD, grounding, sueño, circadiano, motor continuo) debe forzar el motor directamente.
2. Sean **implementables** en el stack actual (Python, Flask demo, headless ticks, NumPy/SciPy, CuPy opcional).
3. Distingan siempre **neuronas LIF activas** vs **ensambles virtuales en disco** vs **connectome lógico**.
4. Prefieran mejoras con **señales observables** (API/HUD, logs, tests) sobre narrativa científica vacía.

Pide a ChatGPT: ideas priorizadas (P0/P1/P2), dependencias, riesgos a la agency, y un sprint de 1–2 semanas concreto.

---

## 1. Qué es Nexo (definición operativa)

**Nexo** es un agente embodied en un mundo 2D doméstico (casa + jardín) con:

- Homeostasis corporal (hambre, sed, temperatura, fatiga, dolor, higiene, vejiga…).
- Percepción (visión resumida, interocepción, olfato/lóbulos, temporal).
- Simulación neuronal LIF (corteza E/I, hipocampo DG–CA3–CA1, columnas por lóbulo).
- Competencia prefrontal–límbica → **15+ schemas de acción discretos** (`choice_key`).
- Ganglios basales / motor; navegación + física biomecánica.
- Memoria episódica en disco (SQLite), ensambles virtuales, scaffold connectómico opcional.
- Sueño NREM/REM con replay.
- Lenguaje opcional (Ollama): **verbaliza**, no planifica.
- Compañera (Nira), ciclo vital, journey heroico, cartas de símbolo, curriculum de neuroanatomía, etc.

**Nombre del repo / workspace:** `cerebro`  
**Clase principal:** `InfantApeBrain` (`brain/mind.py`)  
**Loop:** `NeuralAgentLoop` (`brain/agent_loop.py`)  
**Demo:** Flask `app.py`  
**Experimentos:** `experiments/run_*.py`

---

## 2. Tesis de diseño (no negociable)

| Principio | Implicación |
|-----------|-------------|
| **PFC soberano** | Solo `PrefrontalDeliberation.run` escribe el ganador de acción (`choice_key`). |
| **Sesgos ≠ órdenes** | TD, atención, WM, grounding, circadiano, schemas aprendidos, motor continuo: **sesgan** Go/drives/sensory/heading. |
| **LLM post-hoc** | Ollama/Wernicke–Broca no deben setear motor; E2 midió invarianza headless de trayectorias. |
| **Escala citada con honestidad** | “~50k activas” = LIF en RAM vía `profile_neuron_count`. Millones/billones indexados = disco/scaffold, **no** LIF activos. |
| **Flags** | Features nuevas OFF por defecto en paper batch; ON en demo vía env (`CEREBRO_*`). |

`agency_guard` (health API) documenta explícitamente qué **no** selecciona acciones.

---

## 3. Pipeline de un tick (resumen)

Fases típicas del agent loop:

```
interocept → perceive → cognize (deliberation) → commit → verify → act → learn → (reflect/LLM)
```

Detalles relevantes:

1. **Interocept:** reloj, body.tick, nocicepción, hedonics, **circadian_profile** (si flag), lifecycle plasticity (si flag).
2. **Perceive:** visión, drives merged (body + hedonics + circadian drives + grounding).
3. **Cognize:** cognition + attention budget + WM + consciousness bias + **deliberation PFC–striatum** (+ TD go bias acotado).
4. **Verify:** re-deliberación si spike no alinea (penalty, no override externo).
5. **Act:** walk_goal + motor cortical → decode → `world.apply_motor` (física biomech) + schema_learner.note_success + motor_policy.learn.
6. **Learn:** TD observe; grounding tick decay.

---

## 4. Escalas neuronales (verificadas)

`profile_neuron_count()` = corteza E/I + hipocampo + 4× columnas lobulares.

| Perfil | Nombre | LIF activas (aprox.) | Uso |
|--------|--------|----------------------|-----|
| `COMPACT_PROFILE` | neuro-biológico | **624** | CI, smoke, E4/E5/E7 extendidos |
| `VIRTUAL_LARGE_PROFILE` | neuro-virtual-90M | **1 522** | Demo Flask default |
| `SCALE_10K_PROFILE` | neuro-10k | **10 290** | Paper E1–E3 |
| `SCALE_50K_PROFILE` | neuro-50k | **50 010** | Fase 3; GPU recomendada |

**Capas adicionales (no son LIF activos):**

- Ensambles virtuales en disco (`virtual_assembly.py`) — hasta presupuesto GB; inyección a sensory y opcionalmente a **columnas lobulares** (`inject_to_lobes`).
- Connectome scaffold lógico ~86B (`connectome_blueprint.py`, `cortical_chunks.py`) — flag `enable_connectome_scaffold`.

Bench tick (CPU, sin CuPy disponible en una corrida julio 2026): compact ~16 ms/tick; 10k ~24 ms/tick; 50k omitido sin GPU.

---

## 5. Inventario de capacidades YA implementadas

### 5.1 Núcleo cognitivo / motor

| Capacidad | Módulo(s) | Notas |
|-----------|-----------|-------|
| Deliberación Go/No-Go PFC–límbico | `deliberation.py` | ~15 schemas fijos + aprendidos |
| Goal stack navigate→interact | `goal_stack.py` | |
| Navegación + walk goals | `navigation.py`, `world.py` | |
| Física corporal (fuerzas, gait, agua, ragdoll) | `biomechanics.py` | Fix 2026-07: subpixel motion ya no genera false bumps |
| Intención / spike alignment / veto PFC | `intention.py` | |
| Consciencia / ganador de saliencia | `consciousness.py` | |
| Circuit hub inter-módulo | `circuit_hub.py` | |

### 5.2 Aprendizaje y recompensa

| Capacidad | Flag / env | Notas |
|-----------|------------|-------|
| TD reward V(s,a), δ, go bias ≤0.10 | `enable_td_reward` / `CEREBRO_TD` | Nunca elige winner |
| Schemas aprendidos por consolidación | `enable_learned_schemas` | Entran al menú PFC |
| Motor continuo (heading prior) | `enable_continuous_motor` | Prior; no choice_key |
| Plasticidad por etapa vital | `enable_lifecycle_plasticity` | infant→anciano; poda suave |

### 5.3 Memoria / sueño / atención

| Capacidad | Flag | Notas |
|-----------|------|-------|
| WM limitada (~Miller) | `enable_limited_wm` | Interferencia + damp PFC |
| Atención competitiva presupuesto | `enable_attention_budget` | |
| Sueño selectivo / uniform / default | `enable_selective_sleep` + `replay_mode` | E4 |
| Memoria tipada semantic/procedural | `memory_systems.py` | |
| Prefetch / governor descompresión | `decompression_*.py` | |

### 5.4 Lenguaje y grounding

| Capacidad | Flag | Notas |
|-----------|------|-------|
| Grounding lexicón → drive/sensory/WM | `enable_grounding` / `CEREBRO_GROUNDING` | Nunca choice_key |
| Language cortex + network (Ollama) | `language_*.py` | Post-hoc |
| Tutor RAG / embeddings | `embeddings.py`, tutor | |

**Comportamiento verificado (post-fix física):** con hambre moderada + “mira la nevera”, grounding ON favorece choices foodish y reduce distancia ligeramente vs OFF; el speech en sí no cambia `choice_key`.

### 5.5 Cuerpo / ritmo

| Capacidad | Flag | Notas |
|-----------|------|-------|
| `circadian_profile` (alerta, sleep_drive, cortisol_target, body_temp_target) | `enable_circadian` | S2 hecho |
| Aplica a body fatigue, brainstem sleep_pressure, arousal_bias, hypo cortisol | agent_loop | Expuesto en `time_state`, snapshot, `/api/health` |
| Drives circadianos por fase del día | `apply_circadian_drives` | |

### 5.6 Escala / multimodal

| Capacidad | Flag | Notas |
|-----------|------|-------|
| Perfil 50k | `--profile 50k` | |
| Virtual → lóbulos | `enable_lobe_virtual_inject` | |
| Sensory hub delays + ablation | `enable_multimodal_delays` | E7: world gain 1.0→0.2 sin visión |

### 5.7 Mundo / narrativa / demo

Mundo 2D, food system, TV/web, companion Nira, lifecycle (edad/reproducción), hero journey, cartas de símbolo, curriculum Brain Facts / anatomía, thoughts stream, experience journal, Flask UI + APIs.

---

## 6. Experimentos y métricas (estado)

| Exp | Pregunta | Hallazgo clave (orden de magnitud) | Perfil típico |
|-----|----------|-------------------------------------|---------------|
| E1 | Ablaciones intention | nobind→spike_aligned≈0; nohippo→remembered≈0; nopfc→agency≈0 | 10k |
| E2 | LLM on/off | trayectorias idénticas headless (campos logged) | 10k |
| E3 | Sueño vs control recall | sleep > control (~+8% rel en métrica custom) | 10k |
| E4 | Selective vs uniform sleep | selective ↑ recall total; ventaja emo−neu no siempre clara | compact |
| E5 | Grounding drive | seek_food 0→~0.24; dist_delta pequeño pero ON>OFF tras fix física | compact |
| E7 | Ablate visión | thalamic world gain 1.0→0.2 | compact |
| Bench | ms/tick | CSV + notas HW | compact/10k |

Figuras regenerables: `python -m experiments.plot_figures` → `fig1`–`fig8`.

**Limitaciones experimentales:** métricas custom; n=5; a menudo SD≈0 (determinismo); E2 headless no llama Ollama en ticks; E4/E5/E7 no son aún el harness paper 10k.

---

## 7. Dolores / gaps técnicos reales (prioridad para ideas)

### 7.1 Comportamiento embodied

- Grounding aún produce **acercamiento lento** (física + umbrales de drive + competencia rest/harvest).
- Motor continuo es prior; **no hay política continua entrenada** que resuelva tareas nuevas sin schema.
- Walk goals / attention target a veces compiten o se resetean.

### 7.2 Cognición

- Schemas siguen siendo en gran parte **discretos y diseñados a mano**.
- WM/atención existen pero faltan **tareas duales medibles** en demo.
- Imagination / thoughts poco acoplados a consecuencias motoras.

### 7.3 Percepción

- Visión es gist/foveal simplificada, no CV real.
- Multimodal delays existen; falta **fusión rica** y degradación de tarea por canal con locomoción robusta.
- Audición = eco/encode_text, no espectro real.

### 7.4 Escala / compute

- 50k no medido en GPU real en la máquina de desarrollo reciente.
- Connectome scaffold es procedural; impacto cognitivo todavía limitado.
- Demasiados módulos “ricos” pueden no estar todos activos o visibles en HUD.

### 7.5 Demo / UX

- Muchas señales nuevas en API; **HUD visual incompleto** para circadian, grounding, schemas, agency_guard, TD δ.
- Caregiver UX (voz/cámara) existe parcialmente; grounding no siempre se siente “mágico” en UI.

### 7.6 Ingeniería

- Workspace **no es git repo** en el path OneDrive actual (cuidado con flujos de commit).
- `process_guard` puede matar runners paralelos en Windows.
- Persistencia/meta grande; profile mismatch bloquea load.

---

## 8. Roadmap interno ya cubierto (S1–S7)

| Sprint | Estado |
|--------|--------|
| S1 TD-DA | Hecho |
| S2 Circadiano/fatiga/HUD API | Hecho |
| S3 WM + atención | Hecho |
| S4 Sueño selectivo + E4 | Hecho |
| S5 Grounding + E5 | Hecho |
| S6 Schemas + lifecycle plasticity | Hecho |
| S7 50k + motor continuo + multimodal + bench | Hecho (base); 50k GPU pendiente |

**Paper CLEI:** deliberadamente **aplazado**.

---

## 9. Prompt sugerido para ChatGPT

Copia el artefacto completo y añade:

```text
Eres arquitecto de sistemas cognitivos embodied. Lee el artefacto técnico de Nexo.

Objetivo: proponer un “NIVEL 2 / NEXT GENERATION” del proyecto (no paper).

Restricciones:
- No romper agency: PFC elige choice_key; LLM/TD/grounding/etc. solo sesgan.
- Propuestas implementables en Python/Flask/LIF actual.
- Separar LIF activo vs virtual disco vs scaffold.
- No inventar módulos como existentes si no aparecen en el artefacto.

Entrega:
1) Visión de 1 párrafo del “nuevo nivel”.
2) Top 8 ideas, cada una con: problema que resuelve, cambio de arquitectura, impacto en agency, esfuerzo (S/M/L), dependencia, criterio de éxito medible.
3) Un sprint de 10 días (día a día) eligiendo solo 2–3 ideas P0.
4) 5 ideas “locas pero coherentes” (moonshots) etiquetadas como tal.
5) Anti-patrones: qué NO hacer (hype, millones de neuronas activas falsas, LLM-planner, etc.).
```

Variantes útiles:

- “Optimiza solo **presencia demo** (HUD + comportamiento visible en 30 s).”
- “Optimiza solo **cerebro-likeness** (circuitos), ignorando UI.”
- “Propón una **tarea de navegación emergente** sin schemas nuevos a mano.”
- “Diseña un **modo bebé→adulto** jugable en un día simulado.”

---

## 10. Semillas de ideas (para que el modelo no parta de cero)

Puede expandir / criticar / priorizar:

1. **Affordances espaciales aprendidas** (mapa valor room×object sin schema fijo).
2. **Competencia de predicción** (surprise-driven exploration con free energy light).
3. **Sueño online micro-replay** diurno (ya hay `daytime_replay` — profundizar).
4. **Canal auditivo real** (mic → spectrogram → temporal lobe).
5. **Social bonding closed-loop** con Nira (turn-taking, joint attention).
6. **Curriculum sensorimotor** automático (skills procedurales medibles).
7. **HUD neurofisiológico** unificado (circadian dial, TD δ sparkline, WM slots, agency meter).
8. **Stress test 50k** + governor adaptativo de recall_k.
9. **Episodic → semantic distillation** más agresiva.
10. **Contrastes de ablación en vivo** en demo (toggle flags sin reiniciar).
11. **Intrinsic motivation** (empowerment / novelty search) acotada al Go bias.
12. **Fault injection** (lesiones simuladas: no-hippo, no-PFC) como modo juego/enseñanza.

---

## 11. Archivos ancla (para navegación humana)

```
brain/mind.py                 # orquestador
brain/agent_loop.py           # tick pipeline
brain/deliberation.py         # agency
brain/experiment_flags.py     # feature flags
brain/td_reward.py
brain/grounding.py
brain/environment.py          # circadian_profile
brain/motor_policy.py
brain/sensory_hub.py
brain/learned_schemas.py
brain/lifecycle.py
brain/profile.py              # escalas
brain/world.py + biomechanics.py
app.py                        # demo API
experiments/                  # E1–E7, bench, plot_figures
docs/ROADMAP_CEREBRO_HUMANO.md
```

---

## 12. Checklist de honestidad para cualquier propuesta nueva

- [ ] ¿Quién escribe `choice_key`?
- [ ] ¿Qué flag la apaga en paper/batch?
- [ ] ¿Qué métrica/HUD la hace visible en ≤1 tick de lectura?
- [ ] ¿Confunde LIF con virtual/scaffold?
- [ ] ¿Rompe E1–E3 defaults?
- [ ] ¿Hay test que falle si se fuerza el motor desde el módulo nuevo?

---

*Fin del artefacto técnico. Generado para brainstorming de siguiente nivel — julio 2026. Cifras de perfiles vía `profile_neuron_count`.*
