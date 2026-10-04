# Resumen exhaustivo — proyecto Nexo / `cerebro`

**Artefacto de referencia** · Todo lo implementado, corrido y documentado  
**Paper formal:** [`paper_completo.md`](paper_completo.md) · **Arquitectura:** [`architecture.md`](architecture.md)

---

> **Convención de perfiles:** ver [`perfiles_y_experimentos.md`](perfiles_y_experimentos.md).  
> | Perfil | ~Neuronas | Uso | ¿E1–E3 paper? |
> |--------|-----------|-----|---------------|
> | `COMPACT_PROFILE` | ~500 | CI, smoke, minutos | **No** |
> | `VIRTUAL_LARGE_PROFILE` | ~1.400 | Demo Flask `:5000` | **No** |
> | **`SCALE_10K_PROFILE`** | **~10.290** | Batch GPU | **Sí** |

---

## 1. Visión y tesis del proyecto

**Nexo** es un agente **embodied** (encarnado): vive en un hogar 2D, tiene cuerpo con hambre/sueño/dolor, recorre habitaciones, recuerda episodios y elige acciones como *comer*, *dormir*, *estudiar*, *deambular*.

**Tesis central del paper:**

> Las decisiones y el movimiento salen de circuitos neuronales simulados (PFC–límbico–ganglios basales–hipocampo), **no del LLM**.

Ollama (Mistral, etc.) solo **verbaliza** el estado interno — analogía Broca/Wernicke. Si apagas el LLM, el agente **sigue comportándose igual** (E2: 5/5 seeds idénticos).

Escala: arquitectura **parametrizable** (~500 / ~1.400 / ~10.290 neuronas LIF según perfil). Los **resultados experimentales del paper** usan exclusivamente **`SCALE_10K_PROFILE`**.

---

## 2. Estructura del repositorio

```
cerebro/
├── brain/              # 56 módulos — arquitectura cognitiva completa
├── experiments/        # Harness batch headless + resultados + figuras
├── docs/paper/         # Paper completo, arquitectura formal, borrador EN
├── tests/              # 5 suites de tests
├── app.py              # Demo Flask interactiva (:5000)
├── requirements.txt    # flask, numpy, scipy, pillow, pypdf, matplotlib, cupy
└── data/brain_state/   # Persistencia del demo (no usada en batch)
```

---

## 3. Arquitectura cognitiva implementada (`brain/`)

### 3.1 Núcleo: `mind.py` — `InfantApeBrain`

Clase central (~2200 líneas) que integra todo:

| Capacidad | Descripción |
|-----------|-------------|
| `world_tick()` | Loop autónomo: cuerpo → percepción → deliberación → episodio neural → motor → mundo |
| `_world_tick_headless()` | Versión mínima para experimentos (sin UI, journey, compañero, lenguaje detallado) |
| `_run_episode()` | Episodio neural: recall hipocampal → simulación E/I → gating BG → veto PFC → consolidación |
| `experience()` | Aprendizaje de texto/archivos (E3, currículum) |
| `sleep()` | Sueño NREM: replay ponderado → consolidación cortical → ensambles virtuales |
| `interact()` | Chat con usuario (demo Flask) |
| Modos | `headless`, `auto_save`, `state_dir`, `experiment_flags` |

Hooks de ablación en `_run_episode`: NoBind, NoPFC, NoHippo, NoAffect.

### 3.2 Deliberación — `deliberation.py`

**13 esquemas de acción** (no intents de chatbot):

`eat`, `drink`, `rest`, `sleep`, `tv`, `research`, `study`, `companion`, `hygiene`, `bathroom`, `relief`, `warmth`, `wander`

Cada uno ligado a un **drive** homeostático (`seek_food`, `sleep_need`, `seek_curiosity`, etc.).

Competencia Go/No-Go:

- Canal **límbico**: drives + amígdala + dolor
- Canal **PFC**: working memory + actividad prefrontal
- **GABA** + inhibición prefrontal → No-Go
- **Dopamina** → exploración
- Flag `force_limbic_winner` (ablación NoPFC)

Salidas: `choice_key`, `agency`, `inhibited`, `conflict`, `confidence`, `limbic_winner_key`.

### 3.3 Circuito de intención — `intention.py`

Pipeline post-decisión:

1. `merge_intention_into_sensory` — priming del vector sensorial
2. `prime_prefrontal_wm` — carga WM prefrontal
3. `deliberation_gate_context` — contexto para ganglios basales
4. `enforce_pfc_motor_veto` — veto motor si PFC gana sobre impulso
5. `record_spike_alignment` — métrica `spike_aligned`

Desactivable con `bind_deliberation=False` (ablación NoBind).

### 3.4 Corteza — `cortex.py`, `neuron.py`, `synapse.py`, `inhibition.py`

- Poblaciones LIF: sensory, limbic, associative, prefrontal, motor + interneuronas E/I
- Sinapsis CSR sparse, Hebb + STDP asimétrico
- Ecuaciones en [`architecture.md`](architecture.md)
- GPU: `enable_gpu_matrices()` + spmv en CuPy (`backend.py`)

### 3.5 Hipocampo — `hippocampus_core.py` + `regions.py` + `memory_store.py`

- **DG–CA3–CA1** con sparsity, modulación theta
- **EpisodicMemoryStore** (SQLite): patrones, contexto corporal, habitación, embeddings, tags
- Recall multimodal: similitud patrón + contexto + embedding semántico
- **`record_sleep_replay()`** — refuerza `count` tras replay NREM
- `sample_for_replay()` — replay ponderado por emoción/recencia

### 3.6 Subcortical — `subcortex.py`

| Estructura | Función |
|------------|---------|
| BasalGanglia | Gating Go/No-Go; ruido con `rng_seed=age_ticks` |
| Brainstem | Arousal, presión de sueño |
| Cerebellum | Suavizado motor |
| BrocaArea | Lenguaje motor (demo) |

### 3.7 Afecto y cuerpo

| Módulo | Rol |
|--------|-----|
| `affect.py` | Química sináptica, valencia/arousal subjetivos |
| `body.py` | Hambre, sed, dolor, temperatura, fatiga |
| `regions.py` | Hipotálamo, amígdala, hipocampo wrapper |
| `neurotransmitters.py` | DA, 5-HT, GABA, ACh, NE, cortisol |
| `nuclei.py` | Núcleo accumbens, etc. |

### 3.8 Cognición — `cognition.py`

Ciclo cognitivo con predicción y sorpresa (`mean_surprise` en E1).

### 3.9 Mundo — `world.py`, `navigation.py`, `environment.py`, `vision.py`

- **World2D**: habitaciones, reloj circadiano, objetos
- Agente `(x, y)`, walk goals, estímulos ambientales
- Visión (`scan_world`), olfato inyectable

### 3.10 Memoria extendida — `virtual_assembly.py`

Ensambles indexados en disco (~90M neuronas virtuales posibles con 12 GB). LSH + hot cache.

### 3.11 Lenguaje (no decisional) — `language_cortex.py`, `embeddings.py`

- **LanguageCortex**: Ollama → texto desde `LanguageContext`
- **SemanticEmbedder**: Ollama embed o hash fallback
- En headless: no se invoca; E2 verifica invarianza

### 3.12 Módulos ecológicos / demo

| Módulo | Función |
|--------|---------|
| `companion.py` | Agente social "Nira" |
| `journey.py` | Hero's journey |
| `tarot.py` | Lecturas con memoria |
| `curriculum.py` | Estudio neurociencia |
| `library.py`, `learning_hub.py` | Libros y aprendizaje |
| `imagination.py` | Imaginación interna |
| `web_search.py`, `youtube_tool.py` | Herramientas web |
| `neuroanatomy.py` | Atlas educativo |
| `lobes.py`, `lobe_cortex.py` | Columnas corticales |
| `daytime_replay.py` | Replay diurno |
| `consolidation.py` | Consolidación lenta |
| `persist.py` | Guardado de estado |

### 3.13 Perfiles de escala — `profile.py`

| Perfil | Neuronas activas | Sensory | Motor | Uso | Paper E1–E3 |
|--------|------------------|---------|-------|-----|-------------|
| `COMPACT_PROFILE` | ~500 | 128 | 28 | CI, smoke tests | No |
| `INFANT_APE_PROFILE` | ~340 | 96 | 24 | Bebé-simio | No |
| `VIRTUAL_LARGE_PROFILE` | ~1.400 | 384 | 72 | Demo Flask default | No |
| **`SCALE_10K_PROFILE`** | **~10.290** | 2560 | 320 | Batch GPU, resultados publicados | **Sí** |

Cálculo: corteza E/I + hipocampo + 4× lóbulos (`profile_neuron_count()`).

### 3.14 Ablaciones — `experiment_flags.py`

```python
AblationFlags(
    bind_deliberation=True,      # NoBind → False
    force_limbic_winner=False,   # NoPFC → True
    disable_hippocampus=False,   # NoHippo → True
    disable_affect=False,        # NoAffect → True
)
```

Condiciones: `full`, `nobind`, `nopfc`, `nohippo`, `noaffect`.

### 3.15 Backend GPU — `backend.py` + `experiments/gpu_env.py`

| Variable | Efecto |
|----------|--------|
| `CEREBRO_USE_GPU=1` | Activa CuPy |
| `CEREBRO_GPU_AGGRESSIVE=1` | Cooldown 0 |
| `CEREBRO_GPU_PERSIST=1` | No libera GPU entre episodios |
| `CEREBRO_GPU_MAX_STEPS=999999` | Sin límite pasos GPU |

Hardware: **NVIDIA GeForce RTX 3050 6GB** — `gpu_steps_last_episode=48` en CSV full.

---

## 4. Demo interactiva — `app.py`

- Flask en `:5000`
- UI mapa 2D, chat, estado cerebral, atlas
- Perfil **`VIRTUAL_LARGE_PROFILE`** (~1.4k) + ensambles virtuales — **no** es el perfil de E1–E3
- Separada del harness batch del paper

---

## 5. Harness experimental (`experiments/`)

### 5.1 Scripts

| Archivo | Función |
|---------|---------|
| `run_all.py` | Pipeline: E1 → E2 → E3 → figuras |
| `run_batch.py` | E1 (una condición) o E2 |
| `run_e1_parallel.py` | 5 condiciones E1 en paralelo |
| `run_parallel.py` | Paralelismo manual |
| `run_sleep.py` | E3 sueño vs control |
| `plot_figures.py` | 4 figuras PNG |
| `process_guard.py` | Limpia pipelines duplicados |
| `metrics.py` | TickMetrics + JSONL + CSV |
| `gpu_env.py` | Setup GPU batch |
| `profile_select.py` | Perfil compact/10k/large |
| `ablation_flags.py` | Re-export condiciones |

### 5.2 Métricas (por tick → JSONL; agregadas → CSV)

| Métrica | Significado |
|---------|-------------|
| `agency` | Decisión alineada con motor (0–1) |
| `spike_aligned` | Coherencia spike–decisión (0–1) |
| `pfc_veto` | PFC vetó motor |
| `inhibited` | Impulso límbico inhibido |
| `remembered` | Recall hipocampal exitoso |
| `surprise` | Sorpresa predictiva |
| `drive_coherent` | Acción = drive dominante |
| `choice_key` | Esquema (eat, research, sleep…) |
| `motor` | Índices motores corticales |
| `agent_x/y` | Posición en mundo |

### 5.3 Configuración experimental final

| Parámetro | Valor |
|-----------|-------|
| Perfil | `SCALE_10K_PROFILE` (~10.290 neuronas) |
| Seeds | 5 (0–4) |
| E1 | 200 ticks × 5 seeds × 5 condiciones |
| E2 | 100 ticks × 5 seeds × 2 modos |
| E3 | 4 episodios × 5 seeds × 2 condiciones |
| Headless | Sí |
| GPU E1/E3 | Sí |
| GPU E2 | No (CPU, determinismo) |
| Ollama E1/E3 | Off |

---

## 6. Resultados experimentales

### 6.1 E1 — Ablaciones (medias ± SD, perfil 10k)

| Condición | Agency | Spike aligned | PFC veto | Inhibited | Remembered | Surprise | Drive coherent |
|-----------|--------|---------------|----------|-----------|------------|----------|----------------|
| **full** | 0.132 ± 0.000 | **0.995 ± 0.000** | 0.660 ± 0.000 | 0.660 ± 0.000 | 0.995 ± 0.000 | 1.000 ± 0.000 | 0.293 ± 0.000 |
| **nobind** | 0.132 ± 0.011 | **0.000 ± 0.000** | 0.000 ± 0.000 | 0.661 ± 0.056 | 0.995 ± 0.000 | 0.827 ± 0.000 | 0.248 ± 0.054 |
| **nopfc** | **0.000 ± 0.000** | 0.535 ± 0.018 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.995 ± 0.000 | 0.825 ± 0.004 | **0.913 ± 0.008** |
| **nohippo** | 0.135 ± 0.001 | 0.840 ± 0.051 | 0.675 ± 0.005 | 0.675 ± 0.005 | **0.000 ± 0.000** | 0.837 ± 0.000 | 0.266 ± 0.005 |
| **noaffect** | 0.118 ± 0.001 | 0.506 ± 0.031 | 0.592 ± 0.005 | 0.592 ± 0.005 | 0.995 ± 0.000 | **0.826 ± 0.001** | 0.328 ± 0.004 |

**Interpretación:**

- **NoBind:** spike_aligned → 0 → binding necesario
- **NoPFC:** agency = 0, drive_coherent = 0.91 → impulsos puros
- **NoHippo:** remembered = 0 → ablación limpia
- **NoAffect:** ↓ alignment y surprise

### 6.2 E2 — Invarianza LLM

| Seed | Identical |
|------|-----------|
| 0–4 | **True** (5/5) |

Criterio: `choice_key`, `inhibited`, `pfc_veto`, `motor`.

### 6.3 E3 — Sueño vs control

| Seed | Control | Sleep | Δ |
|------|---------|-------|---|
| 0 | 0.517 | 0.547 | +0.030 |
| 1 | 0.517 | 0.547 | +0.030 |
| 2 | 0.517 | 0.577 | +0.060 |
| 3 | 0.517 | 0.547 | +0.030 |
| 4 | 0.517 | 0.577 | +0.060 |

Promedio: control **0.517**, sleep **0.559** (+8.1%).

Episodios E3:

1. La capital de Francia es París. → `capital Francia`
2. Los neurones disparan potenciales de acción. → `potenciales acción`
3. El hipocampo consolida recuerdos durante el sueño. → `hipocampo sueño`
4. La dopamina refuerza acciones recompensadas. → `dopamina refuerzo`

### 6.4 Figuras

| Archivo | Contenido |
|---------|-----------|
| `experiments/figures/fig1_ablation.png` | Barras E1 |
| `experiments/figures/fig2_spike_alignment.png` | Full vs NoBind |
| `experiments/figures/fig3_llm_invariance.png` | 5/5 identical |
| `experiments/figures/fig4_sleep_recall.png` | Control vs sleep |

---

## 7. Bugs corregidos e ingeniería

| Problema | Solución |
|----------|----------|
| CSV `compute: CPU` con GPU activa | Env leído en runtime (`backend.py`) |
| E2 seed 4 divergía | Semilla BG + E2 en CPU |
| Ruido motor no determinista | `rng_seed=age_ticks` |
| NoHippo KeyError | `memory={"key":"","count":0}` |
| E3 recall = 0 | Score continuo + boost por count |
| Sueño no refuerzaba memoria | `record_sleep_replay()` |
| Pipelines duplicados | `process_guard.py` |
| matplotlib boxplot | `tick_labels=` |
| Lobe cortex tamaño fijo | `n_lobe_per_column` desde perfil |

---

## 8. Documentación producida

| Documento | Descripción |
|-----------|-------------|
| [`paper_completo.md`](paper_completo.md) | Paper detallado con tablas y métodos |
| [`architecture.md`](architecture.md) | Ecuaciones, diagrama, módulo↔región |
| [`draft_workshop.md`](draft_workshop.md) | Borrador corto EN |
| [`resumen_implementacion_completo.md`](resumen_implementacion_completo.md) | Este artefacto |
| [`../../experiments/README.md`](../../experiments/README.md) | Reproducibilidad |

---

## 9. Tests

| Test | Verifica |
|------|----------|
| `test_intention_circuit.py` | Circuito de intención |
| `test_lobes_circuit.py` | Columnas lóbulos |
| `test_lobe_columns_replay.py` | Replay lóbulos |
| `test_curriculum.py` | Currículum |
| `test_web_search.py` | Búsqueda web |

---

## 10. Inventario de artefactos

```
experiments/results/
├── e1_*_summary.csv              (5 condiciones × 5 seeds)
├── e1_*_s{0-4}.jsonl             (25 archivos × 200 ticks)
├── e2_llm_invariance.csv
├── e2_llm_{off,on}_s{0-4}.jsonl
├── e3_sleep_recall.csv
└── pipeline.log

experiments/figures/
├── fig1_ablation.png
├── fig2_spike_alignment.png
├── fig3_llm_invariance.png
└── fig4_sleep_recall.png
```

---

## 11. Comandos de reproducción

```bash
# Pipeline completo
python -m experiments.run_all --profile 10k --seeds 5 --steps 200 --workers 2

# E1 paralelo
python -m experiments.run_e1_parallel --profile 10k --seeds 5 --steps 200 --workers 2

# E2
python -m experiments.run_batch --e2 --profile 10k --seeds 5 --steps 100

# E3
python -m experiments.run_sleep --seeds 5

# Figuras
python -m experiments.plot_figures --in experiments/results

# Limpiar procesos duplicados
python -m experiments.process_guard --orchestrator

# Demo
python app.py
```

---

## 12. Flujo cognitivo (un tick)

```
1. world.advance_clock()        → hora, circadiano
2. body.tick()                  → hambre, sed, dolor
3. vision = scan_world()
4. drives = merge(homeostasis)
5. cognition.run()              → predicción, sorpresa
6. deliberation.compete()       → choice_key
7. [intention] priming sensorial
8. hippocampus.recall()
9. cortex.simulate(N steps)     → spikes E/I
10. basal_ganglia.gate()        → motor
11. [intention] pfc_veto
12. cerebellum.integrate()
13. world.apply_motor()
14. hippocampus.consolidate()
15. [solo demo] language.speak()  → NO decide
```

---

## 13. Síntesis final

| Capa | Qué se hizo |
|------|-------------|
| **Cerebro** | 56 módulos, LIF, hipocampo, PFC–límbico, afecto, mundo 2D |
| **Escala** | Tres perfiles (500 / 1.4k / 10k); **resultados paper = solo 10k** |
| **Experiments** | E1 ablaciones, E2 LLM invariance, E3 sueño, figuras, process_guard |
| **Evidencia** | Binding necesario, PFC → agency, hippo → memory, LLM no decide, sueño ↑ recall |
| **Docs** | Paper completo, arquitectura formal, este resumen, README reproducible |

---

*Generado como artefacto del proyecto Nexo. Datos en `experiments/results/`, figuras en `experiments/figures/`.*
