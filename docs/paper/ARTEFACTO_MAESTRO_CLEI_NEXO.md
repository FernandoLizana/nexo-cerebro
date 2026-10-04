# ARTEFACTO MAESTRO — Nexo / CLEI Electronic Journal

> **Propósito:** única fuente principal verificada para que ChatGPT genere el PDF científico final.  
> **No es el paper.** No contiene maquetación PDF. Toda cifra proviene de código, CSV, JSONL, logs o documentación auditada (julio 2026).

---

# 0. MASTER METADATA

| Campo | Valor verificado |
|-------|------------------|
| **Project name** | Nexo (repositorio: `cerebro`) |
| **Paper title (recommended)** | *Nexo: A Neuro-Inspired Embodied Cognitive Architecture with Simulated Prefrontal–Limbic Action Selection and Non-Decisional LLM Verbalization* |
| **Alternative title 1** | *Embodied Spike-Based Deliberation in Nexo: Ablation Evidence for Intention Binding, Hippocampal Recall, and LLM Invariance* |
| **Alternative title 2** | *Nexo: Functional Analogs of Cortical Competition, Basal Ganglia Gating, and Sleep Replay in a 2D Embodied Agent* |
| **Authors** | TODO — no author block found in repository files |
| **Affiliation** | TODO |
| **City** | TODO |
| **Country** | TODO |
| **Email** | TODO — not present in repo |
| **Results cutoff date** | July 2026 (E1–E3 CSV June 2026; E4/E5/E7 + figures regenerated 2026-07-16) |
| **Artifact version** | 1.1 |
| **Generation date** | 2026-07-16 |
| **Repository** | Local path `cerebro/` — no remote URL verified in workspace |
| **License** | TODO — no project-level LICENSE file found |
| **Main experimental profile** | `SCALE_10K_PROFILE` (`neuro-10k`, **10,290 active simulated neurons**) — **E1–E3** |
| **Extended experiments profile** | `COMPACT_PROFILE` (~624 LIF) — **E4/E5/E7** smoke/extended (not interchangeable with E1–E3 10k) |
| **Demo profile** | `VIRTUAL_LARGE_PROFILE` via `resolve_default_profile()` (**1,522 active neurons**) |
| **Confirmed hardware (experiments)** | NVIDIA GeForce RTX 3050 6GB Laptop GPU (`e1_full_summary.csv`, `pipeline.log`); July 2026 bench ran CPU-only (CuPy unavailable) |
| **Main software** | Python 3 + Flask demo; NumPy/SciPy; optional CuPy CUDA 12 (`requirements-gpu.txt`); SQLite episodic store |
| **Project status** | Active research prototype: Flask demo + headless E1–E7 + figures `fig1`–`fig8` |

---

# 1. EXECUTIVE SUMMARY FOR THE PDF AUTHOR

## Qué es Nexo

Nexo es una **arquitectura cognitiva embodied neuro-inspirada** implementada en Python. Un agente (Nexo) habita un mundo 2D doméstico con habitaciones, objetos y un ciclo día/noche. Posee variables corporales homeostáticas (hambre, sed, temperatura, fatiga, dolor, etc.), percibe el entorno, compite entre canales límbico y prefrontal para elegir entre **15 esquemas de acción discretos**, ejecuta episodios de simulación con **poblaciones LIF** (Leaky Integrate-and-Fire), compuertas de **ganglios basales**, memoria episódica en disco, afecto/neuromodulación, y sueño con replay. Una capa opcional de lenguaje (Ollama/LLM) **verbaliza** estado interno; los experimentos demuestran que, bajo el protocolo headless evaluado, **no altera** deliberación ni motor.

## Qué NO es

- No es un modelo del cerebro humano completo.
- No demuestra consciencia, emociones humanas reales, inteligencia general ni sueño biológico.
- No es un agente LLM-first (tipo ReAct) donde el lenguaje planifica acciones.
- No compite en benchmarks externos (Atari, BabyAI, ACT-R, Nengo) en el estado actual del repositorio.

## Hipótesis central (formulación científica prudente)

> Under the implemented architecture and evaluated experimental conditions, **motor action selection and deliberation emerge from simulated cognitive circuits** (prefrontal–limbic competition, intention binding, basal ganglia gating, hippocampal recall); the **optional LLM layer serves post-hoc verbalization** and, in headless E2, does not change compared trajectory fields.

## Por qué es interesante

Combina: (i) embodied homeostasis en mundo 2D, (ii) spikes LIF a escala ~10k neuronas activas en experimentos, (iii) métricas internas auditables de intención (`agency`, `spike_aligned`, `pfc_veto`, `remembered`), (iv) ablaciones sistemáticas, (v) separación explícita LLM/decisión — tema relevante frente a agentes fundados en LLM.

## Aporte principal defendible

1. Arquitectura integrada open-source con tick pipeline documentado y flags de ablación reproducibles.
2. **E1:** evidencia de ablación sobre métricas internas de circuito de intención.
3. **E2:** invarianza de trayectoria deliberación/motor con `CEREBRO_OLLAMA` on/off (headless).
4. **E3:** mejora del score de recall implementado tras sueño simulado vs control.

## Experimentos y resultados (cifras del CSV)

| Exp | N | Ticks | Resultado clave |
|-----|---|-------|-----------------|
| **E1** | 5 condiciones × 5 seeds × 200 ticks | 200 | `nobind` → `mean_spike_aligned=0`; `nohippo` → `remembered_rate=0`; `nopfc` → `mean_agency=0` |
| **E2** | 5 seeds × 100 ticks × 2 LLM arms | 100 | `trajectories_identical=True` (5/5 seeds) |
| **E3** | 5 seeds × 2 arms × 4 teaching episodes | — | control **0.5174** vs sleep **0.5594** (+0.042 abs, +8.1% rel) |
| **E4** | 5 seeds × 3 arms (compact) | sleep cycles | emotional recall: control **0.712** / uniform **0.808** / selective **0.957** (`e4_sleep_selective.csv`) |
| **E5** | 5 seeds × 2 arms (compact) | 12 | `seek_food` after utter: OFF **0.000** / ON **0.237**; `choice_key` never forced |
| **E7** | 5 seeds × 2 arms (compact) | 20 | thalamic `world` gain: full **1.00** / no_vision **0.20** |
| **E8** | Level 2 causal Arena (compact) | Arena ticks | discriminación: aff_on success **1.0** / ~22 ticks; aff_off **0.0** / timeout (`arena_discrimination.json`, `fig9_e8_causal_arena.png`) |

## Limitaciones principales

- Métricas **custom**, no estándar de psicología/cognición.
- **n=5** seeds; varianza cero en varias condiciones E1/E3/E5/E7 (determinismo fuerte).
- JSONL parcialmente corrupto/incompleto vs CSV (ver §8.7, §19).
- Figuras PNG regeneradas en `experiments/figures/` (`fig1`–`fig9`, 2026-07).
- Demo y experimentos usan **perfiles neuronales distintos**; E4/E5/E7/E8 aquí son **compact**, no 10k (salvo smoke opcional E8).
- E2 en headless **no invoca** Ollama durante ticks; compara campos logueados, no posición explícitamente.
- E4: selective eleva recall emocional **y** neutro; la ventaja diferencial emo−neu no favorece claramente selective vs control (ver CSV).
- E5/E7: `dist_delta`≈0 en el protocolo actual; métricas primarias son drive/talámicas.
- E8: evidencia de mecanismo causal (affordances); no reemplaza E1–E3 10k. Autores/affiliation: ver `docs/paper/AUTHORS.template.md`.

## Narrativa recomendada para ChatGPT

Introducir Nexo como *functional analog* embodied → describir pipeline → presentar RQ1–RQ6 → E1 ablaciones con cautela estadística → E2 acotado a invarianza implementada → E3 como mejora de métrica de recall bajo protocolo → discusión honesta de validez → reproducibilidad con comandos del repo.

---

# 2. VERIFIED PROJECT DESCRIPTION

## 2.1 The embodied agent

| Aspect | Implementation | Source |
|--------|----------------|--------|
| **World** | 2D house + garden; rooms, furniture, objects, TV, desk | `brain/world.py`, `brain/environment.py` |
| **Agent** | Nexo: position `(agent_x, agent_y)`, direction, mood | `world.agent`, `character.py` |
| **Rooms** | e.g. jardín, cocina, baño, dormitorio (Spanish labels) | `world.current_room()` |
| **Objects** | Pickable/harvestable items, fridge, stove, etc. | `food_system.py`, `world.py` |
| **Time** | Day phases: dawn/day/dusk/night; hour | `temporal.py`, `environment.py` |
| **Perception** | Vision summary, attended percepts, drives | `vision.py`, `cognition.py` |
| **Movement** | Walk goals from navigation; motor vector 5-D | `navigation.py`, `world.apply_motor()` |
| **Actions** | 15 discrete schemas → deliberation winner → episode → BG gate | `deliberation.py`, `mind.py` |

## 2.2 Body and homeostasis

Variables in `brain/body.py` (`BodyState`):

| Variable | Range | Role |
|----------|-------|------|
| `hunger` | [0,1] | Drives `seek_food` |
| `thirst` | [0,1] | Drives `seek_water` |
| `body_temp` | [0,1] | Thermal comfort; `seek_warmth` |
| `fatigue` | [0,1] | Drives `seek_rest`, sleep pressure |
| `comfort` | [0,1] | Composite well-being |
| `pleasure` | [0,1] | Hedonic coupling via `hedonics.py` |
| `satiety` | [0,1] | Post-meal state |
| `bladder` | [0,1] | Drives `seek_bathroom` |
| `hygiene` | [0,1] | Drives `seek_hygiene` |
| `pain_head/torso/limbs/ache` | [0,1] each | Nociception; `seek_relief` |
| `total_pain()` | derived | Weighted sum → relief urgency |

Additional embodied layers: `biomechanics.py` (physical fatigue), `nociception.py`, `hedonics.py` (μ-opioid, endocannabinoid analogs).

## 2.3 Cognitive loop (exact tick order)

### Headless (experiments E1–E3) — `agent_loop.py:_run_headless`

| # | Stage | Module | Input | Output | Cognitive role |
|---|-------|--------|-------|--------|----------------|
| 1 | Governor reset | `decompression_governor.py` | tick budget | reset counters | Limits virtual decompression per tick |
| 2 | Interocept | clock, affect decay, body, nociceptor, hedonics | prior state | updated interoception | Homeostatic grounding |
| 3 | Perceive | vision, drives, sleep drive | world, body | attended percepts, drives | Sensory grounding |
| 4 | Cognize | `cognition.py:CognitiveCycle.run` | percepts, modulators | deliberation, prediction | PFC–limbic competition, habits, surprise |
| 5 | Commit | `_phase_commit` → `_run_episode` | sensory + intention | cortical spikes, BG motor | Neural action commitment |
| 6 | Verify | `_phase_verify` | deliberation vs spikes | `spike_aligned`, rechoice | Intention–motor alignment check |
| 7 | Act | `_phase_act` | motor, walk goal | world state delta | Embodied consequence |
| 8 | Prefetch | `decompression_prefetch.py` | memory index | warmed chunks | Virtual assembly prefetch |

### Full demo path adds: echo integration, companion/social, imagination, **`_articulate` (LLM reflect only)** — `agent_loop.py:_run_full` lines 606+.

### Inside `CognitiveCycle.run` (ordered in code)

1. Build percepts → 2. Attention filter → 3. WM/STM → 12. Predictive model → (optional) Global workspace → 9. Reward/surprise → 10. Habits → **4. Deliberation** → emotion regulation → inner dialogue → modulator updates.

### Inside `_run_episode` (`mind.py`)

Intention merge → hippocampal recall → virtual inject → `_simulate` (LIF cortex + hippocampus) → basal ganglia gate → PFC motor veto → spike alignment record → consolidate.

## 2.4 Action schemas (all 15 — `deliberation.py:ACTION_SCHEMAS`)

| Key | Human-readable action | Associated drive | Preconditions (code-verified) | Motor consequence |
|-----|----------------------|------------------|------------------------------|-------------------|
| `eat` | comer | `seek_food` | Contestant included if `limbic≥0.08` or drive present; target fridge | BG gate + walk to fridge; interact motor idx 4 |
| `harvest` | cosechar | `seek_food` | Same threshold; garden context | locomotion + interact |
| `cook` | cocinar | `seek_cook` | Drive from hedonics/craving | stove interact |
| `drink` | beber | `seek_water` | thirst-driven | fridge interact |
| `rest` | descansar | `seek_rest` | fatigue-driven | rest motor pattern |
| `sleep` | dormir | `sleep_need` | brainstem sleep pressure | sleep state transition |
| `tv` | estimularse (TV) | `seek_stimulus` | comfort deficit | TV interact |
| `research` | buscar en la web | `seek_curiosity` | curiosity; desk target | desk navigation |
| `study` | estudiar neurociencia | `seek_curiosity` | curiosity | desk |
| `companion` | acercarse a Nira | `seek_companion` | chemistry/companion boost | approach companion |
| `hygiene` | higiene | `seek_hygiene` | hygiene variable | bath |
| `bathroom` | baño | `seek_bathroom` | bladder | toilet |
| `relief` | atender dolor | `seek_relief` | `pain>0.12` boosts urgency; attended pain | pain relief actions |
| `warmth` | buscar calor | `seek_warmth` | low body_temp | warmth-seeking locomotion |
| `wander` | deambular | (none) | fallback when no contestant | default locomotion |

**Note:** Preconditions are **soft thresholds** in `PrefrontalDeliberation.run`, not hard world gates. World affordances enforced in `world.apply_motor` / event handlers.

---

# 3. VERIFIED ARCHITECTURE

## 3.1 Cortical network (`cortex.py`)

Populations: sensory, limbic, associative, prefrontal, motor + optional interneurons (E/I). Sizes per profile — see §5.

Per 1 ms step: synaptic decay, forward propagation, NMDA gating, PFC→associative inhibition, WM update, homeostatic weight scaling every `homeostasis_every` steps.

## 3.2 LIF equations (`neuron.py:LIFPopulation.integrate`)

\[
\Delta v_i = \frac{-(v_i - v_{\mathrm{rest}}) + I^{\mathrm{syn}}_i + I^{\mathrm{ext}}_i}{\tau_{\mathrm{ms}}} \cdot \Delta t_{\mathrm{ms}}
\]

- Defaults: \(v_{\mathrm{rest}}=-70\), \(v_{\mathrm{thresh}}=-52\), \(v_{\mathrm{reset}}=-75\), \(\tau=20\) ms, \(\Delta t=1\) ms, `refrac_ms=2`.
- Spike when \(v \geq v_{\mathrm{thresh}}\) and not refractory.

## 3.3 Synapses (`synapse.py:SparseSynapses`)

- Format: CSR sparse matrix \(W \in \mathbb{R}^{n_{\mathrm{pre}} \times n_{\mathrm{post}}}\)
- Forward: \(I^{\mathrm{syn}}_j = \sum_i W_{ji} s_i\)
- Density default `synapse_density` per profile (e.g. 0.042 for 10k)

## 3.4 Hebbian plasticity

Trace decay: \(\mathrm{tr} \leftarrow \gamma \mathrm{tr}\), \(\gamma=0.95\).

\[
\Delta w_{ij} = \eta \left( \mathrm{tr}^{\mathrm{pre}}_i \cdot \mathbb{1}[j \in \mathrm{post}] + \mathrm{tr}^{\mathrm{post}}_j \cdot s^{\mathrm{pre}}_i \right)
\]

Clip \(w \in [-w_{\max}, w_{\max}]\), \(w_{\max}=2\).

## 3.5 STDP

\[
\Delta w_{ij} = \eta \cdot \mathrm{tr}^{\mathrm{pre}}_i \cdot \mathbb{1}[j \in \mathrm{post}] - 0.35\eta \cdot \mathrm{tr}^{\mathrm{post}}_j \cdot s^{\mathrm{pre}}_i
\]

**Active when:** `plasticity_step(..., use_stdp=True)` in `cortex.py:tick` on selected synapse pairs, scaled by `plasticity_gate(θ,γ) × plasticity_mult × mods.plasticity_scale()`.

## 3.6 Neuromodulators (`neurotransmitters.py`, `affect.py`, `nuclei.py`)

| Modulator | Range | Functional origin | Used in | Modifies |
|-----------|-------|-------------------|---------|----------|
| Dopamine | [0,1] | VTA/accumbens, reward | deliberation Go, BG exploration, plasticity | go gain, noise, habits |
| Serotonin | [0,1] | raphe analog | conflict damping, amygdala regulation | no-go, conflict |
| Norepinephrine | [0,1] | LC analog | surprise, threat | arousal, attention |
| Acetylcholine | [0,1] | basal forebrain | PFC support, encoding | WM, plasticity gate |
| GABA | [0,1] | interneurons | PFC inhibition | no-go, motor veto |
| Glutamate | [0,1] | excitatory drive | cortical excitation | gain |
| Oxytocin | [0,1] | social bonding | companion, affect | social drives |
| Cortisol | [0,1] | HPA stress | sleep, pain | arousal, serotonin↓ |

## 3.7 Prefrontal–limbic deliberation (`deliberation.py`)

\[
\mathrm{go}_a = \ell_a(0.5 + 0.35\,\mathrm{DA}) + \mathrm{pfc}_a(0.42 + 0.28\,\mathrm{ACh}) + h_a(0.35 + 0.25\,\mathrm{DA})
\]

\[
\mathrm{no\_go}_a = \mathrm{GABA} \cdot \iota_{\mathrm{PFC}} \cdot (0.25 + \mathrm{conflict}) + \text{PFC-inhibit} + 0.06 \cdot \mathrm{surprise}
\]

\[
\mathrm{net}_a = \mathrm{go}_a - \mathrm{no\_go}_a - \mathrm{penalty}_a + \mathcal{N}(0,\, 0.055(1 - 0.45\,\mathrm{DA}))
\]

- **Agency:** \(\mathrm{clip}(\mathrm{pfc}_w / (\ell_w + \mathrm{pfc}_w + 0.15))\), boosted if inhibited.
- **Conflict:** when limbic top ≠ PFC top and both above thresholds.
- **Winner:** `max(net)` unless `force_limbic_winner` (nopfc ablation).

## 3.8 Intention circuit (`intention.py`)

1. Deliberation selects `choice_key`
2. `merge_intention_into_sensory` — blends world/PFC encodings into sensory vector (gain ∝ confidence, agency)
3. `prime_prefrontal_wm` — WM priming (if `bind_deliberation=True`)
4. Episode simulation (`_simulate`)
5. `BasalGanglia.gate` — motor channel selection
6. `enforce_pfc_motor_veto` — blocks impulsive motor if PFC inhibited limbic impulse
7. `record_spike_alignment` — checks overlap between `MOTOR_AFFINITY[choice_key]` and fired/gated channels

## 3.9 Basal ganglia (`subcortex.py:BasalGanglia.gate`)

Scores motor units by membrane potential, spikes, habits, DA, exploration noise; selects top-k channels.

## 3.10 Hippocampus

| Layer | Implementation |
|-------|----------------|
| Spiking DG–CA3–CA1 | `hippocampus_core.py:HippocampalFormation` |
| Episodic store | `memory_store.py` (SQLite + `.npz` patterns) |
| Recall | Pattern similarity + semantic embeddings (`embeddings.py`) + contextual body/room/motor |
| Consolidation | `regions.py:Hippocampus.consolidate`, sleep replay |
| `remembered` flag | `prior is not None` after `hippocampus.recall` in `_run_episode` (`mind.py:1086`) |

## 3.11 Affect (`affect.py:AffectChemistry`)

8 synaptic pools with release/reuptake; `process_stimulus(valence, arousal, novelty, pain, social_bond, attention, surprise)` → modulator sync.

## 3.12 Sleep (`sleep_architecture.py`)

- Triggered by body sleep drive / autonomous mode
- Phases: `nrem_light` → `nrem_deep` (×2) → `rem`
- NREM deep: SWR bursts ×3, `consolidation.consolidate_to_cortex`, `memory_store.record_sleep_replay(key)` increments `count`
- REM: emotional tagging, virtual assembly ingest

## 3.13 Virtual assemblies (`virtual_assembly.py`)

| Concept | What it is | Paper wording |
|---------|------------|---------------|
| **Active LIF neurons** | Simulated each tick | "active simulated neurons" (e.g. 10,290 in E1–E3) |
| **Disk-indexed assemblies** | Sparse engrams (EGR1 codec), LSH recall | "disk-indexed virtual assemblies" |
| **Theoretical capacity** | `disk_GB / 320 bytes × 20 neurons/assembly` | "indexing capacity" — **not** simultaneously active |

At demo default 12 GB budget: ~40.3M assemblies × 20 ≈ **806M logical neurons indexed** (label in profile: "~800M indexadas"). **Do not** call these "90 million active neurons."

## 3.14 Language layer

| Function | Uses LLM? | Can affect action selection? | Evidence |
|----------|-----------|------------------------------|----------|
| `world_tick` headless | No | No | `agent_loop._run_headless` skips `_articulate` |
| `world_tick` full demo | If Ollama available | **No** | `_articulate` after act/learn (`agent_loop.py:606`) |
| `LanguageCortex.express` | If `CEREBRO_OLLAMA=1` | No | Header: "articula estado interno, no decide" |
| `caregiver_speak` | Optional | No motor path | Separate API; episodic micro-loop |
| Semantic embeddings | Ollama embed API | **Indirect** — biases recall input only | `embeddings.py` → hippocampus recall |
| E2 comparison | Flag toggled | **No effect observed** | 5/5 identical trajectories |

`CEREBRO_OLLAMA=0` → `LanguageCortex.enabled=False` → all `_chat()` return None → internal templates.

---

# 4. MODULE-TO-FUNCTION MAP

**Legend:** CE = core evidence; EI = experiment infrastructure; DM = demo/ecological; OU = optional utility.

| File | Main class/function | Cognitive analogy | Computational role | Experiments? | Demo only? |
|------|---------------------|-------------------|----------------------|--------------|------------|
| `mind.py` | `InfantApeBrain` | Whole brain orchestrator | Tick, episode, sleep, API backend | **CE** | shared |
| `agent_loop.py` | `NeuralAgentLoop` | Sensorimotor loop | Headless/full tick pipeline | **CE** | shared |
| `cognition.py` | `CognitiveCycle` | Cognitive cycle | Perceive-attend-deliberate | **CE** | shared |
| `deliberation.py` | `PrefrontalDeliberation` | PFC–limbic competition | Action schema selection | **CE** | shared |
| `intention.py` | merge, veto, alignment | Intention circuit | Sensory binding, spike check | **CE** | shared |
| `cortex.py` | `CorticalNetwork` | Neocortex | LIF populations, plasticity | **CE** | shared |
| `hippocampus_core.py` | `HippocampalFormation` | DG–CA3–CA1 | Spiking hippocampus | **CE** | shared |
| `regions.py` | `Hippocampus`, `Amygdala`… | Limbic regions | Recall, consolidate, arousal | **CE** | shared |
| `memory_store.py` | `EpisodicMemoryStore` | Episodic memory | SQLite persistence, replay count | **CE** | shared |
| `subcortex.py` | `BasalGanglia`, `Brainstem` | BG, brainstem | Gating, sleep pressure | **CE** | shared |
| `affect.py` | `AffectChemistry` | Neuromodulation | Synaptic affect pools | **CE** (noaffect ablation) | shared |
| `neurotransmitters.py` | `NeuromodulatorState` | Global modulators | DA, 5-HT, NE, ACh… | **CE** | shared |
| `experiment_flags.py` | `AblationFlags` | — | Ablations | **EI** | — |
| `sleep_architecture.py` | `SleepArchitecture` | Sleep stages | NREM/REM, replay | **CE** (E3) | shared |
| `consolidation.py` | cortical consolidate | Systems consolidation | Post-replay weights | **CE** (E3) | shared |
| `virtual_assembly.py` | `VirtualAssemblyStore` | Long-term engrams | Disk-indexed patterns | partial | demo-heavy |
| `language_cortex.py` | `LanguageCortex` | Broca/Wernicke analog | Ollama verbalization | **CE** (E2 flag) | shared |
| `language_network.py` | `LanguageNetwork` | Language learning | Tutor, dyad (demo) | no | DM |
| `world.py` | `WorldState` | Environment | 2D physics, rooms | **CE** | shared |
| `body.py` | `BodyState` | Interoception | Homeostasis | **CE** | shared |
| `profile.py` | `NeuroProfile` | Scale profiles | Neuron counts | **EI** | shared |
| `backend.py` | GPU backend | — | CuPy acceleration | **EI** | shared |
| `companion.py` | `Companion` | Social agent Nira | Proximity events | no | **DM** |
| `tarot.py` | tarot draw | — | Narrative toy | no | **DM** |
| `journey.py` | journey arcs | — | Narrative progression | no | **DM** |
| `curriculum.py` | study sections | Education | Neuro curriculum | no | **DM** |
| `brain_facts.py` | chapters | Education | Brain facts study | no | **DM** |
| `web_search.py` | search API | — | External search | no | **DM** |
| `youtube_tool.py` | YouTube | — | Media tool | no | **DM** |
| `neuroanatomy.py` | atlas | Anatomy UI | Visualization | no | **DM** |

*Remaining ~60 `brain/*.py` modules: encoding (`encode.py`), navigation, vision, hedonics, imagination, caregiver dialogue, connectome scaffold, codecs, etc. — mostly **DM/OU** unless wired in headless path.*

---

# 5. SCALE PROFILES

Formula (`profile.py:profile_neuron_count`):

```
total = n_sensory + n_limbic + n_associative + n_prefrontal + n_motor
      + interneurons + n_dg + n_ca3 + n_ca1 + 4 * n_lobe_per_column
interneurons = max(4, n_associative//5) + max(4, n_limbic//5)  [if interneurons=True]
```

| Profile | Active neurons | Sensory | Limbic | Assoc | PFC | Motor | DG/CA3/CA1 | Lobe col | Primary use |
|---------|----------------|---------|--------|-------|-----|-------|------------|----------|-------------|
| `COMPACT_PROFILE` | **624** | 128 | 72 | 112 | 40 | 28 | 40/40/32 | 24 | Smoke tests (`--profile compact`) |
| `VIRTUAL_LARGE_PROFILE` | **1,522** | 384 | 192 | 304 | 112 | 72 | 96/96/72 | 24 | **Flask demo default** |
| `SCALE_10K_PROFILE` | **10,290** | 2560 | 1280 | 2560 | 640 | 320 | 600/600/450 | 128 | **Paper E1–E3** |
| `INFANT_APE_PROFILE` | **519** | 96 | 64 | 96 | 32 | 24 | 28/28/24 | 24 | Alternate small profile |
| `HUMAN_SCAFFOLD_PROFILE` | **10,290** | (same as 10k) | | | | | | 128 | 10k + connectome scaffold metadata |

### Contradiction resolved: "~500", "~1.4k", "~10,290"

| Source says | Verified value | Resolution |
|-------------|----------------|------------|
| "~500 neuronas" (`COMPACT_PROFILE.age_label`) | **624** computed | Use **624** in methods; "~500" is marketing label |
| "~1.4k" (demo) | **1,522** computed | Use **1,522** in methods |
| "~10,290" (paper) | **10,290** computed | **Correct** — use in paper |
| "~340" (`INFANT_APE`) | **519** computed | Do not use 340 |
| "90M neurons" | **~806M logical** at 12 GB disk index | Say "disk-indexed capacity", not active |

---

# 6. RESEARCH QUESTIONS

| RQ | Question | Experiment | Manipulation | Metric | Expected | Actual | Strength |
|----|----------|------------|--------------|--------|----------|--------|----------|
| **RQ1** | Is deliberation→sensory binding necessary for spike–decision alignment? | E1 `nobind` | `bind_deliberation=False` | `mean_spike_aligned` | ↓ vs full | **0.0 vs 0.995** | **Strongly supported** within implementation |
| **RQ2** | Does PFC inhibition modulate agency and drive–action tension? | E1 `nopfc` | `force_limbic_winner=True` | `mean_agency`, `mean_drive_coherent` | agency↓, coherence↑ | **0.0 vs 0.132; 0.913 vs 0.293** | **Supported** |
| **RQ3** | Is hippocampus necessary for episodic recall flag? | E1 `nohippo` | `disable_hippocampus=True` | `remembered_rate` | ↓ vs full | **0.0 vs 0.995** | **Strongly supported** |
| **RQ4** | Does affect modulate surprise and alignment? | E1 `noaffect` | `disable_affect=True` | `mean_surprise`, `mean_spike_aligned` | ↓ | **0.826 vs 1.0; 0.506 vs 0.995** | **Supported** |
| **RQ5** | Does LLM flag change deliberation/motor trajectory? | E2 | `CEREBRO_OLLAMA` 0 vs 1 | `trajectories_identical` | True | **5/5 True** | **Supported** under headless protocol |
| **RQ6** | Does simulated sleep improve recall score? | E3 | sleep 2×80 vs no sleep | `mean_recall` | sleep > control | **0.5594 > 0.5174** | **Supported** (+8.1% rel) |

---

# 7. EXPERIMENTAL METHODS

## 7.1 Common setup

| Parameter | E1 | E2 | E3 |
|-----------|----|----|-----|
| Profile | `10k` → `SCALE_10K_PROFILE` | same | same (via `resolve_experiment_profile()`) |
| Seeds | 0–4 (5) | 0–4 | 0–4 |
| Ticks | 200 | 100 (`min(steps,100)`) | N/A (teach + sleep) |
| Headless | `True` | `True` | `True` |
| `CEREBRO_OLLAMA` | `0` (setdefault) | `0` then `1` | `0` |
| GPU | enabled (`gpu_env.py`) | **forced CPU** | enabled |
| Persistence | temp dir per run | temp dir | temp dir |
| RNG | `np.random.seed(seed)` + `world._rng = default_rng(seed)` | same | same |

## 7.2 Hardware (documented)

- **GPU:** NVIDIA GeForce RTX 3050 6GB Laptop GPU
- **OS:** Windows (from logs/paths)
- **CPU:** not explicitly logged — TODO in paper

## 7.3 Software dependencies

From `requirements.txt`: Flask 3.x, NumPy 1.26+, SciPy 1.11+, Pillow, pypdf, matplotlib 3.8+.  
Optional: `cupy-cuda12x` (`requirements-gpu.txt`).  
Ollama external: `llama3.2:1b` default model.

## 7.4 Reproducibility commands

```bash
# Full pipeline
python -m experiments.run_all --profile 10k --seeds 5 --steps 200 --workers 2

# E1 only
python -m experiments.run_e1_parallel --profile 10k --seeds 5 --steps 200 --workers 2

# E2 only
python -m experiments.run_batch --e2 --profile 10k --seeds 5 --steps 100

# E3 only
python -m experiments.run_sleep --seeds 5

# Figures (requires matplotlib; PNG output)
python -m experiments.plot_figures --in experiments/results
```

## 7.5 Metrics (exact definitions)

| Metric | Source | Computation | Range | Interpretation | Limitations |
|--------|--------|-------------|-------|----------------|-------------|
| `agency` | `deliberation.agency` | PFC share of winner; ↑ if inhibited | [0,1] | Executive override signal | Custom; undefined vs human agency |
| `spike_aligned` | `intention_circuit` | Overlap MOTOR_AFFINITY vs spikes/motor | 0/1 per tick (mean in CSV) | Motor channels match chosen schema | Binary; averaged; nobind→0 by design |
| `pfc_veto` | `intention_circuit` | Motor veto applied | bool | PFC blocked impulsive motor | — |
| `inhibited` | `deliberation.inhibited` | PFC winner ≠ limbic top | bool | Conflict resolution | — |
| `remembered` | tick root | Hippocampal prior found | bool | Episodic hit this tick | Not human recall |
| `surprise` | `cognition.prediction.surprise` | Prediction error | [0,1] | Predictive processing signal | Implementation-specific |
| `drive_coherent` | `metrics.drive_coherence` | 1 if action drive = top drive; 0.5 if curiosity | {0, 0.5, 1} | Action matches dominant drive | Ignores multi-drive nuance |
| `motor` | tick root | BG output channel list | list[int] | Motor command | Compared in E2 |
| `choice_key` | deliberation | Schema key string | 15 labels | Discrete action class | — |
| `agent_x/y` | world | Position | float | Spatial trajectory | **Logged but NOT in E2 identity test** |
| `mean_recall` (E3) | `run_sleep.py:_recall_score` | mean of 4 episode scores | [0,1] | Partial-cue recall strength | Continuous proxy, not binary recall |

### E3 recall score formula

```
score = clip(base_similarity + min(0.36, 0.12 * max(0, count - 1)), 0, 1)
base_similarity = prior.similarity if recall hit else 0.42 (tag fallback) else 0.0
```

Sleep increases `count` via `record_sleep_replay` → higher score.

---

# 8. E1 — ABLATION STUDY

## 8.1 Objective

Quantify contribution of intention-circuit components to internal metrics under autonomous ticking.

## 8.2 Conditions

`full`, `nobind`, `nopfc`, `nohippo`, `noaffect` — **not** `noconscious` (defined in code but no result files).

## 8.3 Exact code manipulation

| Condition | Flag | Code effect | What remains |
|-----------|------|-------------|--------------|
| `full` | defaults | All components on | — |
| `nobind` | `bind_deliberation=False` | Skips `merge_intention_into_sensory` priming | Deliberation, BG, hippocampus |
| `nopfc` | `force_limbic_winner=True` | Limbic always wins if >0.05 | No PFC agency/conflict |
| `nohippo` | `disable_hippocampus=True` | Skips recall/consolidate | Cortical episode intact |
| `noaffect` | `disable_affect=True` | Skips `affect.process_stimulus` | Memory, deliberation |

## 8.4 Experimental size

- 5 conditions × 5 seeds × 200 ticks = **5,000 ticks/condition**, **25,000 total** (if all complete)
- Profile: neuro-10k, 10,290 neurons
- GPU: yes (except noted in CSV columns only for `full` and `nohippo`)

## 8.5 Exact results (from CSV — all seeds)

### `full` (all 5 seeds identical)

| seed | mean_agency | mean_spike_aligned | pfc_veto_rate | inhibited_rate | remembered_rate | mean_surprise | mean_drive_coherent |
|------|-------------|-------------------|---------------|----------------|-----------------|---------------|---------------------|
| 0–4 | 0.132 | 0.995 | 0.66 | 0.66 | 0.995 | 1.0 | 0.2925 |

### `nobind`

| seed | mean_agency | mean_spike_aligned | pfc_veto_rate | inhibited_rate | remembered_rate | mean_surprise | mean_drive_coherent |
|------|-------------|-------------------|---------------|----------------|-----------------|---------------|---------------------|
| 0 | 0.127 | **0.0** | 0.0 | 0.635 | 0.995 | 0.8268 | 0.275 |
| 1 | 0.140 | 0.0 | 0.0 | 0.700 | 0.995 | 0.8268 | 0.210 |
| 2 | 0.115 | 0.0 | 0.0 | 0.575 | 0.995 | 0.8261 | 0.330 |
| 3 | 0.138 | 0.0 | 0.0 | 0.690 | 0.995 | 0.8268 | 0.220 |
| 4 | 0.141 | 0.0 | 0.0 | 0.705 | 0.995 | 0.8271 | 0.205 |
| **mean±SD** | 0.132±0.011 | **0.0±0.0** | 0.0±0.0 | 0.661±0.056 | 0.995±0.0 | 0.827±0.0004 | 0.248±0.054 |

### `nopfc`

| seed | mean_agency | mean_spike_aligned | pfc_veto_rate | inhibited_rate | remembered_rate | mean_surprise | mean_drive_coherent |
|------|-------------|-------------------|---------------|----------------|-----------------|---------------|---------------------|
| 0–1 | **0.0** | 0.52 | 0.0 | 0.0 | 0.995 | 0.8229 | 0.92 |
| 2 | 0.0 | 0.525 | 0.0 | 0.0 | 0.995 | 0.8312 | 0.915 |
| 3–4 | 0.0 | 0.555 | 0.0 | 0.0 | 0.995 | 0.8227 | 0.905–0.908 |
| **mean±SD** | **0.0±0.0** | 0.535±0.018 | 0.0 | 0.0 | 0.995±0.0 | 0.824±0.004 | **0.913±0.008** |

### `nohippo`

| seed | mean_agency | mean_spike_aligned | pfc_veto_rate | inhibited_rate | remembered_rate | mean_surprise | mean_drive_coherent |
|------|-------------|-------------------|---------------|----------------|-----------------|---------------|---------------------|
| 0 | 0.136 | 0.885 | 0.68 | 0.68 | **0.0** | 0.8381 | 0.2625 |
| 1 | 0.135 | 0.885 | 0.675 | 0.675 | 0.0 | 0.8371 | 0.265 |
| 2 | 0.134 | 0.850 | 0.67 | 0.67 | 0.0 | 0.8371 | 0.27 |
| 3 | 0.134 | 0.765 | 0.67 | 0.67 | 0.0 | 0.8371 | 0.27 |
| 4 | 0.136 | 0.815 | 0.68 | 0.68 | 0.0 | 0.8371 | 0.26 |
| **mean±SD** | 0.135±0.001 | 0.840±0.051 | 0.675±0.005 | 0.675±0.005 | **0.0±0.0** | 0.837±0.0004 | 0.266±0.004 |

### `noaffect`

| seed | mean_agency | mean_spike_aligned | pfc_veto_rate | inhibited_rate | remembered_rate | mean_surprise | mean_drive_coherent |
|------|-------------|-------------------|---------------|----------------|-----------------|---------------|---------------------|
| 0–1 | 0.119 | 0.485 | 0.595 | 0.595 | 0.995 | 0.8268 | 0.325 |
| 2 | 0.117 | 0.545 | 0.585 | 0.585 | 0.995 | 0.8258 | 0.3325 |
| 3 | 0.119 | 0.480 | 0.595 | 0.595 | 0.995 | 0.8258 | 0.325 |
| 4 | 0.118 | 0.535 | 0.59 | 0.59 | 0.995 | 0.8258 | 0.33 |
| **mean±SD** | 0.118±0.001 | 0.506±0.031 | 0.592±0.004 | 0.592±0.004 | 0.995±0.0 | 0.826±0.0005 | 0.328±0.004 |

## 8.6 Interpretation by condition

### `nobind`
- **Observation:** `mean_spike_aligned` collapses to 0; `pfc_veto_rate` = 0.
- **Supported:** Binding is necessary for the implemented alignment metric.
- **Do NOT claim:** Binding is necessary for all intelligent behavior or biological intentionality.

### `nopfc`
- **Observation:** `agency=0`, high `drive_coherent≈0.91`, no inhibition.
- **Supported:** PFC channel required for non-zero agency metric; limbic-only → drive-following.
- **Do NOT claim:** PFC creates human free will.

### `nohippo`
- **Observation:** `remembered_rate=0`; other metrics largely preserved.
- **Supported:** Hippocampal module required for `remembered` flag.
- **Do NOT claim:** Complete memory abolition in all subsystems (WM may persist).

### `noaffect`
- **Observation:** ↓ surprise, ↓ spike alignment; memory intact.
- **Supported:** Affect modulates predictive and alignment signals.
- **Do NOT claim:** Emotions are fully removed from behavior (hedonics/body remain).

## 8.7 Statistical caveats

- **n=5** seeds — underpowered for formal inference.
- **Zero SD** in `full` for most metrics → identical trajectories across seeds (strong attractor / deterministic dynamics).
- **No p-values** in repository — do not invent.
- **JSONL integrity issues:** several files truncated or concatenated (`e1_full_s0.jsonl` 157 lines starting tick 43; `e1_nohippo_s0.jsonl` 339 lines). **CSV summaries are the authoritative aggregate** for the paper; note JSONL caveat in limitations.
- Effect sizes (Cohen's d) can be reported descriptively for large gaps (e.g. nobind spike_aligned 0 vs 0.995) but formal tests not run.

---

# 9. E2 — LLM INVARIANCE

## 9.1 Hypothesis

Toggling `CEREBRO_OLLAMA` does not change deliberation or motor trajectories under headless ticking.

## 9.2 Setup

- Condition: always `full`
- Per seed: run 100 ticks with OLLAMA=0, then 100 with OLLAMA=1
- **CPU forced** (`CEREBRO_USE_GPU=0`, `reset_backend()`)
- Fresh temp state dir each arm

## 9.3 What "LLM on" means

`os.environ["CEREBRO_OLLAMA"]="1"` → `LanguageCortex.enabled=True`. In **headless** `world_tick`, **`_articulate` is never called** — Ollama API is not invoked during ticks.

## 9.4 What "LLM off" means

`CEREBRO_OLLAMA=0` → `enabled=False` → internal template fallbacks if language were called.

## 9.5 Compared fields (`run_batch.py:_match`)

- `choice_key`, `inhibited`, `pfc_veto`, `motor`
- **NOT compared:** `agent_x`, `agent_y`, `agency` (logged in traces but excluded from identity test)

## 9.6 Exact results

| seed | steps | trajectories_identical | n_ticks |
|------|-------|------------------------|---------|
| 0 | 100 | **True** | 100 |
| 1 | 100 | True | 100 |
| 2 | 100 | True | 100 |
| 3 | 100 | True | 100 |
| 4 | 100 | True | 100 |

JSONL pairwise inspection (e.g. `e2_llm_off_s0.jsonl` vs `e2_llm_on_s0.jsonl`): identical `choice_key`, `motor`, positions for sampled ticks.

## 9.7 Interpretation

### What E2 demonstrates
- Under headless protocol with fixed seeds, **logged deliberation and motor fields are identical** whether LLM flag is on or off.

### What E2 suggests
- Action selection path does not depend on LLM configuration in this codebase.

### What E2 does NOT demonstrate
- That Ollama never affects behavior in **full demo mode** (where `_articulate` runs).
- That LLM outputs would be identical (no text logged in E2 JSONL).
- That position is identical (not in `_match` — though JSONL shows it matches empirically).
- Causal independence in all future code versions or profiles.

---

# 10. E3 — SIMULATED SLEEP AND RECALL

## 10.1 Hypothesis

Simulated sleep replay increases the implemented recall score vs awake control.

## 10.2 Teaching episodes (`run_sleep.py:TEACHING_EPISODES`)

| # | Text | Query |
|---|------|-------|
| 1 | La capital de Francia es París. | capital Francia |
| 2 | Los neurones disparan potenciales de acción. | potenciales acción |
| 3 | El hipocampo consolida recuerdos durante el sueño. | hipocampo sueño |
| 4 | La dopamina refuerza acciones recompensadas. | dopamina refuerzo |

Protocol per episode: `repeats=2`, `steps_per_repeat=30`.

## 10.3 Control protocol

Teach 4 episodes → measure recall immediately (no sleep).

## 10.4 Sleep protocol

Teach 4 episodes → `brain.sleep(cycles=2, steps_per_cycle=80)` → measure recall.

## 10.5 Recall metric

See §7.5. Continuous score [0,1]; **not** binary recall accuracy. Boost per replay: `+0.12` per count increment, cap `+0.36`.

## 10.6 Exact results by seed

| seed | control | sleep | Δ abs |
|------|---------|-------|-------|
| 0 | 0.5174486802890896 | 0.5474486802890897 | +0.0300 |
| 1 | 0.5174486802890896 | 0.5474486802890897 | +0.0300 |
| 2 | 0.5174486802890896 | 0.5774486802890897 | +0.0600 |
| 3 | 0.5174486802890896 | 0.5474486802890897 | +0.0300 |
| 4 | 0.5174486802890896 | 0.5774486802890897 | +0.0600 |

## 10.7 Aggregate

| Arm | Mean | SD |
|-----|------|-----|
| Control | **0.5174486802890896** | 0.0 |
| Sleep | **0.5594486802890897** | 0.015811388309173894 |
| Δ absolute | **+0.0420000000000002** | — |
| Δ relative | **+8.12%** | — |

## 10.8 Mechanistic explanation

1. `experience()` stores episodes in SQLite with `count` field.
2. `sleep()` → NREM deep → `memory_store.sample_for_replay()` → `record_sleep_replay(key)` → `UPDATE memories SET count = count + 1`.
3. `_recall_score()` adds `min(0.36, 0.12 * (count-1))` to similarity base.
4. Therefore sleep replay **mechanically increases score** even if similarity unchanged.

## 10.9 Limitations

- Metric is **partially tautological** with replay count boost.
- Only 4 Spanish sentences; not general memory benchmark.
- Control mean identical across seeds (0 variance).
- GPU enabled; not tested CPU-only interaction.
- Cannot claim biological sleep benefits — only "simulated sleep replay improved the implemented recall score under this experimental protocol."

---

# 11. FIGURE INVENTORY

| Figure | File (expected) | Exists? | Dimensions | Shows | Data source | Paper location | Caption draft |
|--------|-----------------|---------|------------|-------|-------------|----------------|---------------|
| Fig 1 | `experiments/figures/fig1_ablation.png` | **YES** | 9×4.5 in @150dpi | E1 metrics by condition | `e1_*_summary.csv` | Results §5.1 | "E1 ablation: mean ± SD across 5 seeds (200 ticks, neuro-10k)." |
| Fig 2 | `fig2_spike_alignment.png` | **YES** | — | Spike alignment Full vs NoBind | `e1_full_s*.jsonl` | Results §5.1 | "Spike alignment: full vs nobind." |
| Fig 3 | `fig3_llm_invariance.png` | **YES** | — | E2 identity | `e2_llm_invariance.csv` | Results §5.2 | "E2: trajectory identity LLM off vs on (100 ticks)." |
| Fig 4 | `fig4_sleep_recall.png` | **YES** | — | E3 recall bars | `e3_sleep_recall.csv` | Results §5.3 | "E3: mean recall score control vs sleep (5 seeds)." |
| Fig 5 | `fig5_e4_selective_sleep.png` | **YES** | — | E4 emo/neutral recall | `e4_sleep_selective.csv` | Extended | "E4: selective vs uniform vs control recall (compact, 5 seeds)." |
| Fig 6 | `fig6_e5_grounding.png` | **YES** | — | E5 seek_food bias | `e5_grounding.csv` | Extended | "E5: grounding ON raises seek_food; does not set choice_key." |
| Fig 7 | `fig7_e7_multimodal.png` | **YES** | — | E7 thalamic gain | `e7_multimodal.csv` | Extended | "E7: vision ablation reduces thalamic world gain (1.0→0.2)." |
| Fig 8 | `fig8_bench_tick.png` | **YES** | — | ms/tick by LIF | `bench_tick_gpu.csv` | Methods | "Tick latency compact vs 10k (CPU path, July 2026)." |

**Regenerate:** `python -m experiments.plot_figures --in experiments/results`

---

# 12. TABLE INVENTORY

All tables below are ready for Markdown/LaTeX conversion.

## Table 1 — System components (abbreviated)

| Layer | Module | Function |
|-------|--------|----------|
| Embodiment | world, body | 2D environment, homeostasis |
| Cognition | cognition, deliberation | Perception, action competition |
| Neural | cortex, hippocampus_core | LIF simulation |
| Memory | memory_store | Episodic SQLite |
| Motor | subcortex.BasalGanglia | Gating |
| Language | language_cortex | Post-hoc Ollama (non-decisional) |

## Table 2 — Profiles (see §5)

## Table 3 — E1 results (see §8.5)

## Table 4 — E2 results (see §9.6)

## Table 5 — E3 results (see §10.6–10.7)

## Table 6 — E4 selective sleep (compact, 5 seeds; `e4_sleep_selective.csv`)

| Condition | mean emo recall | mean neu recall | emotion_advantage |
|-----------|-----------------|-----------------|-------------------|
| control | 0.712 ± 0.000 | 0.693 ± 0.000 | +0.018 |
| uniform | 0.808 ± 0.100 | 0.853 ± 0.029 | −0.045 |
| selective | 0.957 ± 0.073 | 0.949 ± 0.044 | +0.007 |

## Table 7 — E5 grounding (compact, 5 seeds)

| Condition | seek_food after speak | choice_key forced |
|-----------|----------------------|-------------------|
| ground_off | 0.000 | False |
| ground_on | 0.237 | False |

## Table 8 — E7 multimodal ablation (compact, 5 seeds)

| Condition | thalamic world gain | occipital gain |
|-----------|---------------------|----------------|
| full_sense | 1.000 | 1.093 |
| no_vision | 0.200 | 0.200 |

## Table 6 — Limitations summary (see §19)

---

# 13. RECOMMENDED FINAL PAPER STRUCTURE (CLEI)

| Section | Objective | Content | Tables | Figures | Pages est. | Avoid claiming |
|---------|-----------|---------|--------|---------|------------|----------------|
| 1. Introduction | Motivate embodied neuro-inspired agents vs LLM-first | Gap, RQ, contributions | — | — | 1.5 | Consciousness, AGI |
| 2. Related Work | Position vs ACT-R, Leabra, Spaun, ReAct | External refs needed | — | — | 1.5 | Nexo superiority |
| 3. Nexo Architecture | Describe pipeline | §2–3 of this artifact | T1, T2 | — | 3 | Exact brain replication |
| 4. Experimental Methodology | Reproducibility | §7 | T-setup | — | 1.5 | p-values not computed |
| 5. Results | E1–E3 | §8–10 | T3–T5 | F1–F4 | 2.5 | Biological sleep |
| 6. Discussion | Interpret cautiously | §8.6–10.9 | — | — | 1.5 | LLM never matters in demo |
| 7. Limitations | Threats to validity | §19 | T6 | — | 1 | — |
| 8. Reproducibility | Commands | §20 | — | — | 0.5 | — |
| 9. Conclusion | Summary | 3–4 sentences | — | — | 0.5 | Hype |
| References | IEEE numbered | §17 | — | — | 1 | Invented DOIs |

**Minimum 12 pages A4** achievable with expanded architecture + limitations.

---

# 14. FULL ABSTRACT CANDIDATES (English, ≤200 words each)

## Abstract A

Nexo is a neuro-inspired embodied cognitive architecture in which a simulated agent inhabits a 2D home environment, maintains homeostatic body variables, and selects among fifteen action schemas through prefrontal–limbic competition, leaky integrate-and-fire cortical dynamics, basal ganglia gating, and hippocampal episodic memory. An optional large language model provides post-hoc verbalization and, under the evaluated headless protocol, does not participate in action selection. We report three in-silico experiments on a 10,290-neuron profile with five random seeds: (E1) ablations show that disabling deliberation binding collapses spike–decision alignment (0 vs 0.995), hippocampal ablation abolishes the remembered flag, and prefrontal ablation removes agency while increasing drive coherence; (E2) LLM on/off yields identical deliberation and motor trajectories; (E3) simulated sleep replay improves a partial-cue recall score from 0.517 to 0.559 (+8.1%). Results support the implementation's functional separation between cognitive circuits and language, but remain limited to custom metrics, a small seed count, and a constrained 2D task suite.

## Abstract B

We present Nexo, an open-source embodied agent coupling homeostatic interoception, spiking neural populations, and an intention circuit with explicit prefrontal veto and spike-alignment verification. Decision-making is implemented as continuous competition over discrete action schemas rather than LLM planning. Experiments (5 seeds, neuro-10k profile) ablate binding, prefrontal bias, hippocampus, and affect, measuring agency, alignment, surprise, and episodic recall flags. Binding ablation reduces mean spike alignment to zero; hippocampal ablation reduces remembered rate to zero; prefrontal ablation zeroes agency. A separate invariance test finds identical motor and deliberation traces with the LLM disabled or enabled in headless mode (100 ticks). Simulated sleep increases an implemented recall score by 0.042 absolute points over awake control. We discuss determinism, zero-variance seeds, and the construct validity of internal metrics. Nexo is best interpreted as a functional analog for studying circuit-level hypotheses, not as a biological brain model.

## Abstract C

This paper describes Nexo, a simulated embodied cognitive architecture integrating homeostatic drives, theta–gamma modulated plasticity, hippocampal episodic storage, and basal ganglia motor gating in a 2D world. Language generation via Ollama is optional and architecturally downstream of motor commitment. We evaluate six research questions using reproducible batch experiments: ablations of intention binding, prefrontal forcing, hippocampus, and affect (200 ticks × 5 seeds); LLM invariance (100 ticks × 5 seeds); and sleep versus control recall (four taught episodes). Key findings: spike alignment depends on binding (mean 0.995 vs 0); remembered episodes require hippocampus (0.995 vs 0); agency requires prefrontal competition (0.132 vs 0); affect modulates surprise and alignment; LLM flag does not change trajectories under headless evaluation; sleep replay improves recall score by 8.1%. Limitations include custom metrics, strong determinism, and absence of external benchmarks.

### RECOMMENDED ABSTRACT

**Abstract A** — most balanced for CLEI: architecture + three experiments + explicit limitations in one flow.

---

# 15. KEYWORDS

**Proposed (12):** embodied cognitive architecture; spiking neural networks; prefrontal–limbic competition; basal ganglia gating; hippocampal memory; sleep replay; ablation study; homeostatic agents; neuromodulation; intention circuit; large language models; reproducible simulation

**Recommended (7):** embodied cognitive architecture; spiking neural networks; action selection; hippocampal memory; ablation study; sleep replay; language model invariance

---

# 16. INTRODUCTION EVIDENCE PACK

| Element | Content for ChatGPT |
|---------|---------------------|
| **Problem** | LLM agents conflate language with policy; need architectures where motor choice is auditable and circuit-based |
| **Gap** | Few embodied spike-based testbeds with systematic ablations + LLM invariance tests at ~10k scale |
| **Motivation** | Separate decision from verbalization; measure intention metrics under ablation |
| **Hypothesis** | Circuits suffice for action selection; LLM is post-hoc; sleep replay improves recall metric |
| **Contributions** | (1) Integrated open-source architecture (2) E1 ablation battery (3) E2 LLM invariance (4) E3 sleep recall (5) Reproducible scripts |

---

# 17. RELATED WORK REQUIREMENTS

## References already present and verified (in `paper_completo.md`)

1. Anderson, J. R., et al. (2004). An integrated theory of the mind. *Psychological Review*. [DOI TODO — research externally]
2. O'Reilly, R. C., & Munakata, Y. (2000). *Computational Explorations in Cognitive Neuroscience*. MIT Press. [ISBN TODO]
3. Eliasmith, C., et al. (2012). A large-scale model of the functioning brain. *Science*, 338(6111), 1202–1205. [DOI: 10.1126/science.1225268 — verify]
4. Yao, S., et al. (2023). ReAct: Synergizing reasoning and acting in language models. *ICLR 2023*. [verify]

## References mentioned but incomplete

- Leabra / emergent — cited in prose, no full bib entry
- Nengo / Spaun toolchain
- Active inference / Friston — not in bib
- Global Workspace (Baars/Dehaene) — in `consciousness.py` comments only

## Must be researched externally

- Cognitive architectures survey
- Hippocampal replay (e.g. Wilson & McNaughton 1994; Girardeau et al.)
- Basal ganglia action selection models
- Embodied AI benchmarks
- LLM agent safety / tool-use papers beyond ReAct

---

# 18. CLAIM AUDIT

| Claim | Evidence | Strength | Safe wording | Unsafe wording |
|-------|----------|----------|--------------|----------------|
| LLM does not decide | E2 + code path | Strong (headless) | "LLM did not change logged deliberation/motor fields in E2" | "LLM never influences Nexo" |
| Binding necessary | E1 nobind | Strong (metric) | "Binding ablation abolished spike alignment metric" | "Binding is necessary for consciousness" |
| PFC creates agency | E1 nopfc | Supported (metric) | "Agency metric requires PFC competition" | "PFC creates free will" |
| Hippocampus enables memory | E1 nohippo | Strong (remembered flag) | "Hippocampal module required for remembered flag" | "Without hippocampus Nexo cannot learn" |
| Affect modulates surprise | E1 noaffect | Supported | "Affect ablation reduced surprise metric" | "Nexo has real emotions" |
| Sleep improves recall | E3 | Supported (custom score) | "Simulated sleep replay improved recall score" | "Sleep improves memory like humans" |
| Nexo is scalable | Profiles 624–10290 | Implementation-dependent | "Multiple profiles from 624 to 10,290 active neurons" | "Scales to human brain" |
| 10k neurons | CSV `n_neurons=10290` | Direct | "10,290 active simulated neurons" | "10k biological neurons" |
| 90M virtual neurons | profile label | Misleading | "disk-indexed assemblies up to ~800M logical units" | "90 million active neurons" |
| GPU acceleration | `backend.py`, logs | Direct (optional) | "Optional CuPy GPU for cortical steps" | "Real-time brain simulation" |
| Determinism | E1/E3 zero SD | Direct | "Several conditions showed identical seeds" | "Fully deterministic brain model" |
| Reproducibility | scripts exist | Supported | "Batch scripts provided" | "Independent replication confirmed" |

---

# 19. LIMITATIONS AND THREATS TO VALIDITY

## Internal validity

- Custom metrics may not measure intended constructs.
- JSONL/CSV mismatch; some JSONL corrupted.
- `noconscious` condition not reported.

## Construct validity

- `agency`, `spike_aligned`, `remembered` are operational definitions, not clinical/psychological constructs.
- E3 recall score mechanically coupled to replay count.

## External validity

- 2D house world only; 15 schemas; no transfer to other environments.
- No comparison to ACT-R, Nengo, or RL baselines.

## Statistical validity

- n=5; no hypothesis tests; zero variance in controls.
- Independence across seeds assumed but dynamics may be attractor-dominated.

## Biological fidelity

- LIF + STDP are simplified; rates not calibrated to neurophysiology.
- "Prefrontal", "limbic" are functional analogs.

## Software engineering

- Flask demo ≠ experiment profile.
- Ollama optional dependency not version-pinned.
- `pytest` not in requirements.txt.

## Experimental design

- E2 headless → LLM never actually called.
- E2 does not assert position in code (though JSONL matches).
- Figures not generated in repo snapshot.
- Pipeline log incomplete (stopped mid-E2 in one run).

---

# 20. REPRODUCIBILITY PACKAGE

| Experiment | Command | Input | Output | Runtime |
|------------|---------|-------|--------|---------|
| Full | `python -m experiments.run_all --profile 10k --seeds 5 --steps 200 --workers 2` | profile, seeds | `experiments/results/e1_*.csv`, `e2_*.csv`, `e3_*.csv` | **TODO** — not logged |
| E1 | `python -m experiments.run_e1_parallel --profile 10k --seeds 5 --steps 200 --workers 2` | flags via condition | `e1_{cond}_summary.csv`, `e1_{cond}_s{seed}.jsonl` | — |
| E2 | `python -m experiments.run_batch --e2 --profile 10k --seeds 5 --steps 100` | OLLAMA 0/1 | `e2_llm_invariance.csv`, `e2_llm_{on,off}_s*.jsonl` | — |
| E3 | `python -m experiments.run_sleep --seeds 5` | teaching episodes | `e3_sleep_recall.csv` | — |
| Figures | `python -m experiments.plot_figures --in experiments/results` | CSV | `experiments/figures/fig*.png` | seconds |
| Clean | `python -m experiments.process_guard` | — | kills orphan processes | — |

**Environment variables (experiments):**

```
CEREBRO_EXPERIMENT_PROFILE=10k
CEREBRO_OLLAMA=0          # E1, E3 default
CEREBRO_USE_GPU=1         # E1, E3 (E2 forces 0)
CEREBRO_GPU_AGGRESSIVE=1
CEREBRO_GPU_PERSIST=1
CEREBRO_GPU_MAX_STEPS=999999
```

**Seeds:** 0, 1, 2, 3, 4 (integer seed for `numpy` and `world._rng`).

---

# 21. PDF PRODUCTION INSTRUCTIONS FOR CHATGPT

## Page format

- A4, **one column**, **10 pt** body, Times New Roman or equivalent, single spacing, numbered pages.

## First page

- Title 16 pt centered
- Authors 12 pt
- Affiliation, email (TODO fields)
- Abstract ≤200 words (**Abstract A** recommended)
- Keywords (7 recommended)

## Figure placement

| Figure | After paragraph |
|--------|-----------------|
| Fig 1 | "Ablation results show condition-specific degradation..." (Results E1) |
| Fig 2 | Optional: spike alignment time series discussion |
| Fig 3 | "LLM invariance experiment..." (Results E2) |
| Fig 4 | "Sleep replay increased recall score..." (Results E3) |

## Table placement

- Table 2 (profiles): Section 3 Architecture
- Table 3 (E1): Section 5 Results
- Table 4–5: Section 5
- Table 6 (limitations): Section 7

## Caption rules

- Figures: caption **below**, numbered.
- Tables: caption **above**, numbered.
- All referenced before appearance.

## Bibliography

- IEEE numeric, order of citation, add DOI/URL when verified externally.

## Visual style

- Sober grayscale figures; no marketing styling; legible axis labels (regenerate figures before PDF).

---

# 22. FINAL DATA BLOCK FOR AUTOMATED PDF GENERATION

```yaml
paper:
  project_name: Nexo
  recommended_title: "Nexo: A Neuro-Inspired Embodied Cognitive Architecture with Simulated Prefrontal–Limbic Action Selection and Non-Decisional LLM Verbalization"
  authors:
    - TODO
  affiliations:
    - TODO
  emails:
    - TODO
  language: en
  page_size: A4
  columns: 1
  body_font_size: 10pt
  abstract_word_limit: 200

experiment_main:
  profile: SCALE_10K_PROFILE (neuro-10k)
  active_neurons: 10290
  seeds: 5
  e1_ticks: 200
  e2_ticks: 100
  gpu: true
  gpu_model: "NVIDIA GeForce RTX 3050 6GB Laptop GPU"

results:
  e1:
    full:
      mean_agency: 0.132
      mean_spike_aligned: 0.995
      remembered_rate: 0.995
      mean_surprise: 1.0
      mean_drive_coherent: 0.2925
    nobind:
      mean_spike_aligned: 0.0
      mean_agency: 0.132
    nopfc:
      mean_agency: 0.0
      mean_drive_coherent: 0.913
    nohippo:
      remembered_rate: 0.0
      mean_spike_aligned: 0.840
    noaffect:
      mean_spike_aligned: 0.506
      mean_surprise: 0.826
  e2:
    trajectories_identical: "5/5 seeds True"
    ticks: 100
    fields_compared: [choice_key, inhibited, pfc_veto, motor]
  e3:
    control_mean: 0.5174486802890896
    sleep_mean: 0.5594486802890897
    delta_absolute: 0.0420000000000002
    delta_relative_percent: 8.12

figures:
  - id: fig1
    path: experiments/figures/fig1_ablation.png
    caption: "E1 ablation metrics (mean ± SD, 5 seeds, 200 ticks, neuro-10k)."
    section: Results
    exists: true
  - id: fig2
    path: experiments/figures/fig2_spike_alignment.png
    caption: "Spike alignment: full vs nobind."
    section: Results
    exists: true
  - id: fig3
    path: experiments/figures/fig3_llm_invariance.png
    caption: "E2 LLM on/off trajectory identity."
    section: Results
    exists: true
  - id: fig4
    path: experiments/figures/fig4_sleep_recall.png
    caption: "E3 recall score: control vs simulated sleep."
    section: Results
    exists: true
  - id: fig5
    path: experiments/figures/fig5_e4_selective_sleep.png
    caption: "E4 selective vs uniform vs control recall (compact, 5 seeds)."
    section: Extended
    exists: true
  - id: fig6
    path: experiments/figures/fig6_e5_grounding.png
    caption: "E5 grounding ON raises seek_food; never sets choice_key."
    section: Extended
    exists: true
  - id: fig7
    path: experiments/figures/fig7_e7_multimodal.png
    caption: "E7 vision ablation: thalamic world gain 1.0→0.2."
    section: Extended
    exists: true
  - id: fig8
    path: experiments/figures/fig8_bench_tick.png
    caption: "Tick latency by active LIF profile (CPU path)."
    section: Methods
    exists: true

tables:
  - id: tab_profiles
    caption: "Neural scale profiles and active neuron counts."
    section: Architecture
  - id: tab_e1
    caption: "E1 ablation results (mean ± SD across 5 seeds)."
    section: Results
  - id: tab_e2
    caption: "E2 LLM invariance outcomes."
    section: Results
  - id: tab_e3
    caption: "E3 sleep vs control recall by seed."
    section: Results
  - id: tab_e4
    caption: "E4 selective sleep recall (compact)."
    section: Extended
  - id: tab_e5
    caption: "E5 grounding drive bias (compact)."
    section: Extended
  - id: tab_e7
    caption: "E7 multimodal vision ablation (compact)."
    section: Extended
  - id: tab_limitations
    caption: "Summary of limitations and threats to validity."
    section: Limitations

missing_information:
  - item: Author names and affiliations
    impact: Required for CLEI submission — must be supplied by user
  - item: Project LICENSE
    impact: Legal clarity for open distribution
  - item: Git repository URL
    impact: Reproducibility statement
  - item: Formal statistical tests / p-values
    impact: Cannot claim significance without analysis
  - item: CPU model and RAM for experiments
    impact: Hardware reproducibility section incomplete
  - item: E4/E5/E7 on SCALE_10K_PROFILE
    impact: Extended results currently compact-only; not interchangeable with E1–E3
  - item: Complete pipeline.log for full run
    impact: Partial verification of end-to-end pipeline timing
```

---

*End of artefacto maestro. All numerical results trace to `experiments/results/*.csv` unless marked as computed from `brain/profile.py`. Contradictions between docs and data resolved per hierarchy: CSV > code > `paper_completo.md`.*
