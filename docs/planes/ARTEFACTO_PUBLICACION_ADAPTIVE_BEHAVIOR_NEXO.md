# ARTEFACTO — Publicación Adaptive Behavior (SAGE) · NEXO / cerebro

| Campo | Valor |
|-------|-------|
| **Target journal** | *Adaptive Behavior* (SAGE) — Article |
| **Project** | Nexo (repository: `cerebro`) |
| **Author** | Fernando Andrés Lizana Núñez |
| **Affiliation** | Digital Rider SpA, Chile |
| **Artifact version** | 1.0 |
| **Audit date** | 2026-07-22 |
| **Results cutoff** | July 2026 (E1–E3 CSV June 2026; E4/E5/E7 + Arena present) |
| **Evidence root** | `publication_evidence/` |
| **Secondary docs** | `docs/paper/ARTEFACTO_MAESTRO_CLEI_NEXO.md`, `paper_completo.md`, `paper_causal_affordances.md` |
| **Rule** | No invented results/DOI/refs. Tags: **VERIFIED** / **PARTIALLY VERIFIED** / **PROPOSED** / **NOT YET TESTED** / **EVIDENCE MISSING** |

**Naming collision (critical):** CLEI **E4** = selective sleep (`e4_sleep_selective.csv`). **E8 / Level 2** = causal Arena affordances (`arena_*.json`). Do not conflate.

**Neural counts (runtime-verified):** `COMPACT_PROFILE` = **624** active LIF; `VIRTUAL_LARGE_PROFILE` = **1,522**; `SCALE_10K_PROFILE` = **10,290**. Marketing labels “~500 / ~1.4k / ~10k” are approximate; manuscripts should prefer exact counts. Virtual disk assemblies ≠ active neurons.

---

# 1. Executive Summary

## Español

NEXO es una arquitectura cognitiva *embodied* neuro-inspirada (agente en hogar 2D) donde drives homeostáticos, competencia prefrontal–límbica y gating de ganglios basales seleccionan entre 15 esquemas de acción. Un LLM opcional (Ollama) verbaliza estado; **no escribe** la acción motora. La auditoría de código confirma que el único escritor de `choice_key` es `PrefrontalDeliberation.run` (`brain/deliberation.py`).

Evidencia en repositorio: ablaciones E1 (10 290 LIF, 5 seeds), invarianza LLM E2 (5/5 trayectorias idénticas), recall tras sueño E3 (control ≈0.517 vs sleep ≈0.547–0.577), sueño selectivo E4, grounding E5, multimodal E7 (compact), y Arenas Level 2 / E8 (affordances on vs off). Faltan baselines externos, estadística inferencial, N≥20, benchmarks públicos y figuras PNG regeneradas.

**SUBMISSION READINESS: 42/100.** Encaje temático plausible; evidencia experimental insuficiente para *Article* en Adaptive Behavior sin trabajo mayor.

## English

NEXO is a neuro-inspired embodied cognitive architecture: a simulated agent in a 2D home whose homeostatic drives, prefrontal–limbic competition, and basal-ganglia gating select among 15 discrete action schemas. An optional LLM verbalizes internal state but does not write motor decisions. Static inspection and unit tests support that **`PrefrontalDeliberation` is the sole writer of `choice_key`**.

Available evidence includes E1–E3 on `SCALE_10K_PROFILE` (10,290 active LIF), compact E4/E5/E7, and Level-2 causal Arena (E8). Missing elements for Adaptive Behavior include comparative baselines, inferential statistics, larger seed sets, ecological framing, and regenerated figures. Honest readiness score: **42/100** — recommendation **C. REQUIRES MAJOR EXPERIMENTAL WORK**.

### Score breakdown (verifiable)

| Criterion | Score / weight | Notes |
|-----------|----------------|-------|
| Architecture clarity + agency boundary | 16/20 | VERIFIED in code/tests |
| Adaptive Behavior topical fit | 8/15 | Fit after reframing; weak ecology |
| Experimental completeness | 6/25 | Ablations yes; baselines/stats no |
| Statistical rigor | 2/15 | Means only; n=5; often zero variance |
| Reproducibility package | 6/15 | Scripts/CSV yes; lockfile/figures no |
| Manuscript maturity | 4/10 | Drafts exist; AB framing incomplete |
| **Total** | **42/100** | |

---

# 2. Journal Fit: Adaptive Behavior

Adaptive Behavior publishes work on adaptive and autonomous systems, embodied cognition, and biologically inspired computation interacting with environments. NEXO’s homeostasis → deliberation → motor loop is thematically aligned **if** reframed as adaptive action selection under internal regulation—not as a “digital brain.”

## Strong Fit Elements

- Embodied agent with body variables and environmental consequences (**VERIFIED**: `brain/body.py`, `brain/world.py`).
- Action selection under competing drives (**VERIFIED**: `brain/deliberation.py`).
- Learning that biases selection without usurping it (affordances/TD/grounding) (**VERIFIED**: module headers + tests).
- Sleep/replay affecting memory metrics (**PARTIALLY VERIFIED**: E3/E4 CSVs; metric custom).

## Weak Fit Elements

- Heavy internal circuit metrics (`agency`, `spike_aligned`) vs ecological survival/adaptation scores.
- 2D symbolic home, not physical robot or rich ecology.
- No published external baselines (**EVIDENCE MISSING**).
- Profile mixing (10k vs compact) risks confusion if not stated.

## Desk-Rejection Risks

1. Reads as software/architecture report without comparative adaptive behavior.
2. Custom metrics without external validation.
3. Overclaim risk (brain / consciousness language in older docs).
4. Small N + deterministic identical seeds.
5. Insufficient related-work DOIs (**EVIDENCE MISSING** in this package).

## Required Reframing

Lead with **adaptive homeostatic action selection** and **agency-preserving bias pathways**. Demote LLM to post-hoc verbalization. Explicitly deny human-brain simulation claims. Elevate Arena Level-2 tasks and planned baselines to the center of the narrative.

---

# 3. Scientific Problem

| Element | Statement | Status |
|---------|-----------|--------|
| **General problem** | How can an artificial agent adaptively select actions under homeostatic pressure while keeping a clear, auditable decision boundary? | PROPOSED framing |
| **Gap** | Many LLM agents conflate language with action; many RL agents lack explicit agency auditability. | Literature map incomplete — EVIDENCE MISSING for exhaustive survey |
| **Limitation of existing stacks** | Opaque planners; language-as-policy; weak embodiment. | Conceptual |
| **RQ** | Under NEXO’s architecture, do PFC–limbic deliberation and bounded bias modules (affordance/TD/grounding) yield adaptive behavior without non-PFC writers of `choice_key`? | PROPOSED |
| **H1 (primary)** | Ablating PFC / binding / hippocampus selectively impairs corresponding internal metrics (E1). | PARTIALLY VERIFIED in CSV |
| **H2** | LLM on/off does not alter logged deliberation/motor trajectories (E2). | VERIFIED in `e2_llm_invariance.csv` |
| **H3** | Sleep condition improves implemented recall metric vs control (E3). | PARTIALLY VERIFIED (small Δ, custom metric) |
| **H4** | Affordance learning improves Level-2 Arena success vs off (E8). | PARTIALLY VERIFIED (compact; small N) |
| **IVs** | Ablation flags, Ollama on/off, sleep arm, affordances on/off, profile | VERIFIED in code |
| **DVs** | agency, spike_aligned, remembered_rate, recall scores, Arena success/ticks, seek_food_after_speak | VERIFIED metrics code |
| **Confounds** | Profile scale, determinism, metric circularity, headless LLM non-invocation | Documented |

---

# 4. Claimed Contributions

### Architectural

| ID | Contribution | Status | Evidence | Repository Location | Novelty Risk | Validation Needed |
|----|--------------|--------|----------|---------------------|--------------|-------------------|
| A1 | Integrated embodied LIF + deliberation + BG gate loop | VERIFIED | code | `mind.py`, `agent_loop.py`, `cortex.py` | Medium (integration vs novelty) | External comparison |
| A2 | Sole `choice_key` writer = `PrefrontalDeliberation` | VERIFIED | code+tests | `deliberation.py` | Medium | Agency-break ablation |
| A3 | Bounded Go biases (affordance ±0.08, TD ≤0.10) | VERIFIED | code | `affordance_map.py`, `td_reward.py` | Medium | Sensitivity analysis |
| A4 | Optional LLM verbalization outside motor path | VERIFIED | E2+code | `language_cortex.py`, E2 CSV | Low–medium | Interactive LLM path audit |

### Experimental

| ID | Contribution | Status | Evidence | Location | Novelty Risk | Validation Needed |
|----|--------------|--------|----------|----------|--------------|-------------------|
| E1c | Ablation matrix on intention metrics (10k) | PARTIALLY VERIFIED | CSV | `e1_*_summary.csv` | Medium | Stats + larger N |
| E2c | LLM trajectory invariance (headless) | VERIFIED under protocol | CSV | `e2_llm_invariance.csv` | Medium | Live Ollama ticks |
| E3c | Sleep recall improvement | PARTIALLY VERIFIED | CSV | `e3_sleep_recall.csv` | Medium | Ecological recall |
| E8c | Causal affordance Arenas | PARTIALLY VERIFIED | JSON | `arena_*.json` | Medium | Multi-seed + baselines |

### Methodological / Software / Conceptual

| ID | Contribution | Status | Evidence | Location | Novelty Risk | Validation Needed |
|----|--------------|--------|----------|----------|--------------|-------------------|
| M1 | Flag-driven ablations (`AblationFlags`) | VERIFIED | code | `experiment_flags.py` | Low | Document defaults |
| S1 | Reproducible experiment scripts | PARTIALLY VERIFIED | scripts+CSV | `experiments/` | Low | Lockfile |
| C1 | Agency-preserving adaptive selection framing | PROPOSED | this artifact | — | High if overclaimed | Peer review |

---

# 5. Repository Evidence Audit

| Scientific Claim | Evidence Type | File Path | Class/Function | Evidence Strength | Notes |
|------------------|---------------|-----------|----------------|-------------------|-------|
| Embodied agent class | code | `brain/mind.py` | `InfantApeBrain` | strong | VERIFIED |
| World motor apply | code | `brain/world.py` | `apply_motor` | strong | VERIFIED |
| Body homeostasis | code | `brain/body.py` | `Body` / `BodyState` | strong | VERIFIED |
| LIF dynamics | code | `brain/neuron.py` | `LIFPopulation.integrate` | strong | VERIFIED |
| Sole `choice_key` write | code | `brain/deliberation.py` | `PrefrontalDeliberation.run` | strong | `choice_key=winner.key` |
| Tick pipeline | code | `brain/agent_loop.py` | `NeuralAgentLoop` | strong | VERIFIED |
| Ablation flags | code | `brain/experiment_flags.py` | `AblationFlags` | strong | Many extras default OFF |
| Affordance bias only | code+test | `brain/affordance_map.py` | `biases_for` | strong | `AFFORDANCE_BIAS_MAX=0.08` |
| TD bias only | code+test | `brain/td_reward.py` | `go_biases` | strong | `TD_GO_BIAS_MAX=0.10` |
| Grounding bias only | code+test | `brain/grounding.py` | apply helpers | strong | Never sets `choice_key` |
| HUD agency_guard declarative | code | `brain/causal_hud.py` | `build_causal_hud` | medium | Not a formal proof |
| Sleep architecture | code | `brain/sleep_architecture.py` | `SleepArchitecture` | strong | E3/E4 |
| Language cortex | code | `brain/language_cortex.py` | `LanguageCortex` | strong | Optional LLM |
| Metrics | code | `experiments/metrics.py` | `drive_coherence` | strong | Custom |
| E1–E7 / Arena results | csv/json | `experiments/results/` | — | strong/partial | See §9 |
| Figures PNG | filesystem | `experiments/figures/` | — | none | **EVIDENCE MISSING** at audit |
| External baselines | — | — | — | none | **EVIDENCE MISSING** |
| Author credentials beyond name | — | — | — | none | Use only provided identity |

Full machine-readable map: `publication_evidence/evidence_inventory.csv`.

---

# 6. Architecture Reconstruction

Reconstructed exclusively from repository code (secondary docs used only as cross-check).

## 6.1 Environment

- **In:** agent pose, rooms, objects, day phase. **Out:** percept summaries, interaction outcomes.
- **Modules:** `brain/world.py`, `brain/environment.py`, `brain/navigation.py`.
- **Can commit action?** No — executes motor after deliberation.
- **Evidence:** VERIFIED. **Limits:** 2D symbolic home; not physical robotics.

## 6.2 Body and Homeostasis

- **State:** hunger, thirst, body_temp, fatigue, comfort, pleasure, satiety, bladder, hygiene, pain channels (`brain/body.py`).
- **Update:** per tick / interaction. **Can commit action?** No — raises drives.
- **Evidence:** VERIFIED.

## 6.3 Perception

- Vision/attended percepts (`vision.py`, `cognition.py`); thalamic gains (E7).
- **Can commit?** No. **Limits:** summarized/symbolic sensors.

## 6.4 Neural Dynamics

- Cortical LIF populations + sparse synapses (`cortex.py`, `neuron.py`, `synapse.py`).
- Profiles set population sizes (`profile.py`). Episode simulation in `mind.py`.
- **Can commit?** Spikes feed BG gate / alignment — motor after gate, not independent schema choice.

## 6.5 Attention and Working Memory

- Cognitive cycle attention filter + WM (`cognition.py`); optional limited WM flag.
- **Can commit?** No.

## 6.6 Episodic / Hippocampal Memory

- DG/CA3/CA1 sizes per profile; recall into episode (`mind.py`, hippocampus modules).
- **Can commit?** No — can bias context/recall.

## 6.7 Learning and Value Signals

- Habits, TD (`td_reward.py`, flag OFF by default), affordance map (`affordance_map.py`), hedonics.
- **Can commit?** No — bounded Go/drive biases when enabled.

## 6.8 Sleep / Offline Replay

- `sleep_architecture.py`; E3 sleep vs control; E4 selective/uniform/control.
- **Can commit waking action?** No during offline protocol.

## 6.9 Language and Grounding

- `language_cortex.py` (Ollama optional); `grounding.py` biases drives/sensory.
- **Can commit?** No (**VERIFIED** headers + `test_grounding.py`; E5 `choice_key_forced_by_grounding=False`).

## 6.10 Prefrontal / Deliberative Action Selection

- `PrefrontalDeliberation.run`: limbic vs PFC contestants → net Go/No-Go → winner → **`choice_key=winner.key`**.
- **Sole schema commitment writer** under audited paths (**VERIFIED**).

## 6.11 Motor Execution

- Intention / BG gate / PFC veto / `world.apply_motor` (`intention.py`, `agent_loop.py`, `world.py`).
- Continuous motor policy (`motor_policy.py`) may bias locomotion when flagged — **does not write `choice_key`** (**VERIFIED** header pattern; continuous path **NOT YET TESTED** as publication table).

## 6.12 Logging, Auditability, Reproducibility

- Tick metrics → JSONL/CSV (`experiments/metrics.py`); causal HUD (`causal_hud.py`); experiment runners under `experiments/`.
- **agency_guard:** declarative dict in HUD, not a formal verifier (**VERIFIED**).

---

# 7. Agency-Preservation Analysis

### Decision flow (implemented)

```
Environment → Perception → Internal state (body/affect/drives)
  → Candidate influences (habits, TD, affordances, grounding, recall, penalties)
  → PrefrontalDeliberation (writes choice_key)
  → Episode / BG gate / veto / spike alignment
  → Motor execution (apply_motor)
```

Evidence:
- File: `brain/deliberation.py`
- Symbol: `PrefrontalDeliberation.run` → `DeliberationResult(choice_key=winner.key)`
- Verification: static inspection + agency-related unit tests
- Status: **VERIFIED**

| Component | Can Bias Action? | Can Directly Commit Action? | Can Bypass Deliberation? | Code Evidence | Risk |
|-----------|------------------|-----------------------------|--------------------------|---------------|------|
| TD reward | Yes (Go ≤0.10) | No | No | `td_reward.py` | Low if flag documented |
| Affordance map | Yes (±0.08) | No | No | `affordance_map.py` | Low |
| Grounding | Yes (drives/sensory) | No | No | `grounding.py` | Low |
| LLM / language cortex | Verbalization | No | No (headless E2) | `language_cortex.py`, E2 | Medium if interactive path untested |
| Hippocampal recall | Context bias | No | No | mind episode path | Low |
| Circadian | Flagged | No | No | flags | Low |
| Continuous motor | Locomotion prior | No `choice_key` | Partial locomotion influence | `motor_policy.py` | Medium |
| Reflexes | Arousal/attention | No | No | `reflexes.py` | Low |
| `force_limbic_winner` | Forces limbic contestant | Yes (ablation) | Replaces PFC winner | `deliberation.py` + flags | Intentional ablation |
| External commands / UI | Demo path | Possible via API | Demo not paper path | `app.py` | Exclude from claims |
| `agency_guard` HUD | N/A | N/A | N/A | declarative only | Do not claim formal proof |

**Finding:** Under paper/headless experimental paths audited, **PFC deliberation is the sole writer of `choice_key`**. Bias modules are agency-preserving by design. There is **no formal proof system**—only code conventions, HUD declarations, and unit tests. Agency-break control experiment: **MISSING** (see M5).

---

# 8. Neural-Scale Honesty Audit

Computed: `profile_neuron_count` → 624 / 1522 / 10290 (**VERIFIED** runtime 2026-07-22).

| Representation | Actual Dynamic Simulation? | Update Frequency | State Variables | Cost | Scientific Interpretation |
|----------------|----------------------------|------------------|-----------------|------|---------------------------|
| Active LIF populations | Yes | Episode ms steps | v, spikes, synapses | High at 10k | Report exact counts |
| Interneurons (if enabled) | Yes | Same | included in count | Medium | Part of active total |
| Hippocampus DG/CA3/CA1 | Yes | Episode | population states | Medium | Active LIF subset |
| Virtual assemblies on disk | No (indexed retrieve/inject) | On recall | engrams SQLite/disk | Disk I/O | **≠ neurons** |
| Connectome scaffold logical nodes | No full dynamics | Inject gain | logical target ~86B | Cache | Conceptual scaffold only |
| `agency` float | Metric | Per deliberation | scalar | Negligible | Internal ratio, not consciousness |

**Do not claim:** millions/billions of simulated neurons from disk/scaffold. Demo “~1.4k + disk” must separate active LIF (1,522) from indexed assemblies.

---

# 9. Existing Experimental Evidence

| Experiment | Hypothesis | Conditions | N/Seeds | Metric | Result (repo) | Evidence Path | Reproducible? |
|------------|------------|------------|---------|--------|---------------|---------------|---------------|
| **E1 full** | Intact circuit yields non-zero agency / alignment | full @10k | 5×200 ticks | mean_agency, spike_aligned | agency≈0.132; spike_aligned=0.995 (identical seeds) | `e1_full_summary.csv` | Yes (scripts) |
| **E1 nopfc** | No PFC → agency 0 | nopfc | 5 | mean_agency | **0.0**; veto 0 | `e1_nopfc_summary.csv` | Yes |
| **E1 nobind** | No binding → spike_aligned 0 | nobind | 5 | spike_aligned | **0** (per CLEI audit / CSV) | `e1_nobind_summary.csv` | Yes |
| **E1 nohippo** | No hippo → remembered_rate 0 | nohippo | 5 | remembered_rate | **0** | `e1_nohippo_summary.csv` | Yes |
| **E1 noaffect** | Affect ablation | noaffect | 5 | summary metrics | Present | `e1_noaffect_summary.csv` | Yes |
| **E2** | LLM on/off invariance | 100 ticks | 5 | trajectories_identical | **True** 5/5 | `e2_llm_invariance.csv` | Yes; headless caveat |
| **E3** | Sleep improves recall metric | control vs sleep | 5×4 ep | mean_recall | control **0.5174**; sleep **0.547–0.577** | `e3_sleep_recall.csv` | Yes |
| **E4** | Selective sleep helps emotional recall | control/uniform/selective @compact | 5 | emo/neu recall | selective elevates both; emo advantage inconsistent | `e4_sleep_selective.csv` | PARTIAL |
| **E5** | Grounding raises food drive after utter | on/off @compact | 5×12 | seek_food_after_speak | OFF **0**; ON **0.2367**; forced=False | `e5_grounding.csv` | PARTIAL (dist≈0) |
| **E7** | Vision ablation changes thalamic gain | full vs no_vision | 5×20 | thalamic_world_gain | 1.00 vs **0.20**; distances unchanged | `e7_multimodal.csv` | PARTIAL |
| **E8 Arena thirst** | Aff on returns after exposure | aff on/off @compact | small N | success/timeout | Present JSON | `arena_thirst_unknown_water.json` | PARTIAL |
| **E8 discrimination** | Prefer good vs dry fountain | aff on/off | seeds 0–1+ | drank_success | on **true**/22 ticks; off **false**/110 | `arena_discrimination.json` | PARTIAL |
| Bench | Tick cost | compact/10k | — | ms/tick | CSV | `bench_tick_gpu.csv` | Yes |

**Not experiments:** Flask demo HUD; virtual disk size demos.

**Hardware noted in E1 CSV:** NVIDIA GeForce RTX 3050 6GB Laptop GPU. Code version pin: **EVIDENCE MISSING** (no git tag cited in CSV).

---

# 10. Ablation Study Matrix

| Ablation | Scientific Question | Control | Expected Selective Effect | Metric | Current Status |
|----------|---------------------|---------|---------------------------|--------|----------------|
| Episodic / hippo | Is recall needed for remembered_rate? | full | remembered_rate ↓ | E1 | DONE (CSV) |
| PFC / deliberation | Is agency PFC-dependent? | full | agency → 0 | E1 | DONE |
| Intention binding | Is spike_aligned binding-dependent? | full | spike_aligned → 0 | E1 | DONE |
| Affect | Does affect change surprise/drives? | full | metric shifts | E1 | DONE (interpret carefully) |
| LLM | Does language change trajectories? | Ollama off | no change | E2 | DONE headless |
| Sleep | Does offline replay help recall? | no-sleep | recall ↑ | E3 | DONE small Δ |
| Selective sleep | Emotional prioritization? | uniform/control | emo advantage ↑ | E4 | PARTIAL / mixed |
| Grounding | Utterance → drive bias? | ground_off | seek_food ↑ | E5 | PARTIAL |
| Vision | Sensory gain drop? | full_sense | thalamic gain ↓ | E7 | PARTIAL (no behavior Δ) |
| Affordances | Causal Level-2 learning? | aff_off | success ↑ | E8 | PARTIAL |
| TD direct policy | What if TD writes actions? | bias-only | coherence/agency change | — | **MISSING** (baseline) |
| Homeostasis off | Need body drives? | full | survival ↓ | — | **MISSING** |
| WM / attention flags | Capacity effects? | flags | TBD | — | **NOT YET TESTED** as paper tables |
| Agency-break | Boundary value? | allow force choice_key | violations ↑ | — | **MISSING** |

---

# 11. Required Baselines

| # | Baseline | Minimal implementation | Hold constant | Metrics | Fairness risk |
|---|----------|------------------------|---------------|---------|---------------|
| 1 | Rule-reactive | argmax drive → fixed schema | world, body physics | survival, homeostatic deviation, goals | Hand-tuned rules may be strong |
| 2 | No-memory | disable hippo/episodic write-read | ticks, seeds | recall, adaptation latency | Must not disable unrelated systems |
| 3 | No-homeostasis | freeze body vars / zero drives | perception | survival meaningless — redefine task | Task redesign needed |
| 4 | No-deliberation | `force_limbic_winner` or random schema | motor API | agency, coherence, goals | Already partial via nopfc |
| 5 | Learner-direct policy | TD/RL picks `choice_key` | reward definition | goals + agency violations | Defines contrast for agency claim |
| 6 | Full NEXO | all paper defaults | — | all | Reference |

**Status:** All comparative baselines **EVIDENCE MISSING** as published tables (nopfc is an ablation, not a full baseline suite).

---

# 12. Experimental Plan Before Submission

**Design principles:** prefer compact for power (n=20–30); reserve 10k for key confirmatory arms; never mix profiles in one results table; redirect outputs to `publication_evidence/logs/`.

### Experiments A–J (proposed)

| ID | Question | Design sketch | Success criterion (PROPOSED) |
|----|----------|---------------|------------------------------|
| A | Survival / homeostasis | 30 seeds; baselines 1,3,6; long horizon | Lower cumulative |drive error| vs reactive |
| B | Environmental change | Move water/food mid-run | Faster reacquisition with memory/affordance |
| C | Memory recovery | E3-like + behavioral probe | Sleep > control on probe |
| D | Action selection | Contest logging vs rule agent | Higher goal completion under conflict |
| E | Sensory degradation | Extend E7 with behavior metrics | Performance drop when vision ablated |
| F | Sleep/replay | E3/E4 + stats | Significant effect + CI |
| G | Grounding | E5 longer horizon | Approach food (distance↓) not only drive |
| H | Language invariance | E2 + interactive articulate ticks | Document scope; identical or quantify Δ |
| I | Agency boundary | Force LLM/TD write choice_key | Violations rise; coherence may rise short-term |
| J | Scalability | bench compact/10k/50k | Report ms/tick; no quality claim without behavior |

**Statistics:** bootstrap 95% CI; Wilcoxon or permutation paired by seed; effect sizes (rank-biserial / Cliff’s δ); Holm correction across primary DVs. **Do not invent p-values here.**

**Pseudo-protocol:** fix `CEREBRO_EXPERIMENT_PROFILE`; set seeds 0..N-1; run condition matrix; write CSV under dated folder; refuse overwrite of `experiments/results/` publication assets.

Commands: see `publication_evidence/reproduction_commands.md`.

---

# 13. Metrics Dictionary

| Name | Definition | Range | Better | Implementation | Limits |
|------|------------|-------|--------|----------------|--------|
| `agency` | `winner.pfc/(limbic+pfc+0.15)` (+boost if inhibited) | [0,1] | context-dependent | `deliberation.py` | Internal; ≠ free will |
| `spike_aligned` | Intention–spike alignment | [0,1] | higher if binding claim | intention circuit / metrics | Custom |
| `remembered_rate` | Fraction ticks with recall flag | [0,1] | higher for memory claim | E1 summaries | Ablation-defined |
| `drive_coherence` | 1 if action drive = top drive | {0,0.5,1} | task-dependent | `metrics.drive_coherence` | Curiosity special-cased |
| `mean_recall` (E3) | Protocol recall score | ~[0,1] | higher | sleep experiment | Implementation-defined |
| `emotion_advantage` (E4) | emo − neu recall | ℝ | selective >0 hoped | E4 CSV | Often ~0 / negative |
| `seek_food_after_speak` | Drive after grounding utter | [0,1] | higher if grounding works | E5 | Not locomotion |
| `trajectories_identical` | Logged field equality LLM on/off | bool | True for invariance | E2 | Not full physics audit |
| `drank_success` / ticks | Arena completion | bool / int | success; fewer ticks | arena JSON | Small N |
| `agency_violations` | Count of illegal writers | ≥0 | 0 | arena logs | Depends on instrumentation |
| survival time | Time until critical failure | ticks | higher | **PROPOSED** | Not in current CSV |
| homeostatic deviation | ∫|setpoint−state| | ≥0 | lower | **PROPOSED** | Not formalized |

---

# 14. Statistical Analysis Plan

**PROPOSED** (no fabricated statistics):

1. Per-seed primary DV; report median + IQR and mean ± SD.
2. Bootstrap CI (10 000 resamples) for mean differences.
3. Prefer non-parametric paired tests across matched seeds.
4. Effect sizes mandatory beside p-values.
5. Pre-register primary DV per experiment (one) to limit multiplicity; Holm for secondary.
6. Report zero-variance seeds explicitly (E1 full identical rows — strong determinism).
7. Failed seeds: log and exclude with criterion stated a priori.
8. Power: with n=5 and σ≈0, inference is not population-level — raise n before claims.

---

# 15. Reproducibility Checklist

| Item | Status |
|------|--------|
| Controlled seeds in runners | COMPLETE (scripts accept `--seeds`) |
| `requirements.txt` | PARTIAL (ranges; no lockfile) |
| `requirements-gpu.txt` | PARTIAL |
| Python version pinned in paper | MISSING |
| OS documented | PARTIAL (dev on Windows in this audit) |
| Hardware in E1 CSV | COMPLETE for that run |
| Datasets / CSV results | COMPLETE under `experiments/results/` |
| Scripts | COMPLETE |
| Commands documented | COMPLETE → `publication_evidence/reproduction_commands.md` |
| Logs archive | PARTIAL |
| License | MISSING (no project LICENSE found in CLEI audit) |
| README experiment section | PARTIAL |
| Containers | MISSING |
| Unit tests | COMPLETE (agency-related subset runnable) |
| Auto tables/figures | PARTIAL (`plot_figures.py`; PNGs MISSING) |

---

# 16. Figure Plan

| Figure | Scientific message | Data needed | Source | Status | Misread risk |
|--------|-------------------|-------------|--------|--------|--------------|
| F1 | Architecture overview | modules | code | Design only | Overclaim “brain” |
| F2 | Agency-preserving pipeline | bias caps | deliberation + flags | Design | Imply formal proof |
| F3 | Body–environment loop | body vars | body/world | Design | Ecology overstated |
| F4 | Ablation design | E1 conditions | CSV | Data ready | Profile confusion |
| F5 | Main behavioral / Arena | arena JSON | results | PARTIAL data | n small |
| F6 | Sleep/memory | E3/E4 | CSV | Data ready | Metric ≠ biology |
| F7 | Scalability | bench CSV | `bench_tick_gpu.csv` | PARTIAL | Equate speed with intelligence |
| F8 | Failures / determinism / limits | identical seeds | E1/E5/E7 | Design | Hide weaknesses |

**PNG files:** **EVIDENCE MISSING** in workspace at audit. Regenerate via `python -m experiments.plot_figures` into `publication_evidence/figures/` without inventing data.

---

# 17. Table Plan

| Table | Content | Status |
|-------|---------|--------|
| T1 | Module I/O summary | Can draft from §6 |
| T2 | Profile parameters + neuron counts | VERIFIED numbers |
| T3 | Experiment protocols | From runners |
| T4 | E1–E3 primary results | CSV-backed |
| T5 | Ablation matrix | §10 |
| T6 | Baseline comparison | **EMPTY until run** |
| T7 | Hardware/runtime | E1 + bench |
| T8 | Limitations | §27 |

---

# 18. Manuscript Blueprint

Target: **6 000–12 000 words**, Adaptive Behavior Article.

| Section | Words | Focus |
|---------|-------|-------|
| Abstract | ≤250 | Adaptive selection + agency boundary + verified results only |
| Introduction | 800–1 200 | Problem; gap; RQ; contributions |
| Related Work | 900–1 300 | Architectures, homeostasis, action selection, SNNs, grounding |
| Architecture | 1 200–1 800 | Honest scale; pipeline; bias vs commit |
| Methods | 1 000–1 500 | Profiles, protocols, metrics, stats plan |
| Results | 900–1 400 | E1–E3; compact extensions; Arena; **no baselines yet** |
| Discussion | 800–1 200 | Interpretation bounds |
| Limitations | 300–600 | Mandatory honesty |
| Conclusion | 250–450 | Conservative |

**Working English title structure:** Introduction → Related Work → System Architecture → Experimental Methods → Results → Discussion → Limitations → Conclusion.

---

# 19. Proposed Title

1. **Recommended:** *Agency-Preserving Action Selection in an Embodied Homeostatic Agent: The NEXO Architecture*
2. *Adaptive Behavior under Prefrontal–Limbic Competition in NEXO: Ablations and Causal Affordances*
3. *Bounded Learning Signals and Auditable Deliberation in a Spiking Embodied Agent*
4. *Separating Verbalization from Motor Choice in NEXO: Evidence from Ablations and Level-2 Arenas*
5. *Homeostatic Drives, Spike-Gated Gating, and Non-Decisional Language in NEXO*

**Why #1:** Centers Adaptive Behavior keywords (agency, action selection, embodiment, homeostasis) without claiming human-brain simulation.

---

# 20. Abstract Draft

Large language model agents often conflate linguistic generation with motor choice, obscuring who selects actions. We present **NEXO**, a neuro-inspired embodied cognitive architecture in which homeostatic drives, prefrontal–limbic competition, and basal-ganglia gating select among discrete action schemas in a simulated 2D home. Optional language generation verbalizes internal state but is architected not to write the motor decision variable `choice_key`; static inspection and unit tests identify `PrefrontalDeliberation` as that variable’s sole writer. Using configurable active LIF scales (624; 1,522; 10,290 neurons), we report ablations of prefrontal control, intention binding, and hippocampal recall on internal circuit metrics (profile 10,290; five seeds), headless invariance of logged trajectories with language enabled versus disabled, a modest sleep-related gain on an implemented recall score, and compact-profile Arena tasks where bounded causal affordance biases improve discrimination and return-after-exposure relative to affordances off. We do not claim biological consciousness or human-brain fidelity. Comparative ecological baselines and inferential statistics required for strong adaptive-behavior claims remain future work.

**Word count:** 198.

---

# 21. Keywords

1. cognitive architecture  
2. adaptive behavior  
3. embodied artificial intelligence  
4. action selection  
5. homeostatic agents  
6. spiking neural networks  

(All six represent real project axes; trim to journal limit if needed.)

---

# 22. Introduction Draft

Artificial agents that act in environments must continually select actions under changing external conditions and internal needs. In many contemporary systems, a single language model both narrates and decides, which makes it difficult to audit how homeostatic pressures, memory, and learning contribute to behavior. Classical cognitive architectures and biologically inspired controllers offer clearer modules, yet connecting mesoscale spiking dynamics, explicit deliberation, and optional language without collapsing them into one opaque policy remains challenging.

This article presents **NEXO**, an embodied agent inhabiting a simulated domestic environment. Bodily variables generate drives; a prefrontal–limbic competition forms a discrete action choice; neural episodes and basal-ganglia gating support motor commitment; sleep and learning modules update memory and bounded evidence for future choices. Language, when enabled, articulates state after the fact rather than authoring `choice_key`.

**Research question.** Can an integrated architecture demonstrate (i) selective dependence of internal control metrics on deliberation, binding, and memory, (ii) language invariance of logged motor deliberation under a headless protocol, and (iii) improved Level-2 Arena behavior when causal affordances bias—but do not override—deliberation?

**Contributions (conservative).** (1) An auditable agency boundary implemented in code. (2) An ablation suite on a 10,290-LIF profile. (3) Compact Arena evidence for affordance-biased adaptation. (4) An explicit limitations and missing-baseline agenda for Adaptive Behavior.

**Organization.** Section 2 surveys related areas [DETAIL REQUIRED: verified citations]. Section 3 describes architecture and scale honesty. Section 4 methods. Section 5 results from repository evidence. Section 6 discussion and limitations.

---

# 23. Related Work Map

**Policy:** No invented bibliography. Entries below are **categories to populate** with DOIs verified by the author before submission. Status: **EVIDENCE MISSING** until DOIs attached.

| Category | Placeholder focus | Relation to NEXO | Diff | DOI/URL | Status |
|----------|-------------------|------------------|------|---------|--------|
| Cognitive architectures | ACT-R, Soar, CLARION-style surveys | Modular cognition | NEXO adds LIF episode + explicit choice_key boundary | — | EVIDENCE MISSING |
| Embodied cognition | Synthetic agents / enactivism reviews | Body–world loop | Simulated 2D home only | — | EVIDENCE MISSING |
| Adaptive agents | Adaptive Behavior journal classics | Homeostatic adaptation | Need ecological metrics | — | EVIDENCE MISSING |
| Action selection | Basal-ganglia / contest models | PFC–limbic contest | Functional analog, not biophysical BG | — | EVIDENCE MISSING |
| Homeostatic agents | Drive-reduction robots | Body vars | Discrete schemas | — | EVIDENCE MISSING |
| Biologically inspired AI | Neuromorphic / BICA | Inspiration | Mesoscale not whole-brain | — | EVIDENCE MISSING |
| Spiking nets | LIF / SNN toolkits | LIFPopulation | Small scale vs neuromorphic chips | — | EVIDENCE MISSING |
| Episodic memory | Hippocampal models | DG/CA3/CA1 sizes | Highly simplified | — | EVIDENCE MISSING |
| Sleep and replay | Systems consolidation models | E3/E4 protocols | Custom recall metric | — | EVIDENCE MISSING |
| Language grounding | Grounded language agents | Grounding biases drives | Never writes choice_key | — | EVIDENCE MISSING |
| Explainability / agency | XAI / accountability | HUD + tests | Declarative guard ≠ proof | — | EVIDENCE MISSING |

Secondary in-repo drafts (`docs/paper/*`) may list names; **do not copy unverified citations into the submission**.

---

# 24. Methods Draft

**Environment.** Simulated 2D home with rooms and interactable objects (`brain/world.py`). Agent pose updated via motor commands.

**Agent.** `InfantApeBrain` with body state, cognition cycle, deliberation, cortex, hippocampus, optional language (`brain/mind.py`).

**Observations.** Vision summaries, drives, interoception — not raw camera pixels [DETAIL REQUIRED: exact observation vector schema per experiment].

**Actions.** 15 schemas in `ACTION_SCHEMAS` (`deliberation.py`); winner `choice_key` executed through episode + `apply_motor`.

**Architecture.** See §6. Profiles: compact 624, virtual 1,522, 10k 10,290 active LIF (`profile_neuron_count`).

**Simulation cycle (headless).** Governor → interocept → perceive → cognize (deliberation) → commit/episode → verify → act → prefetch (`agent_loop.py`).

**Experiments.** E1–E3: `--profile 10k`, 5 seeds (existing CSV). E4/E5/E7/Arena: compact. Flags via `AblationFlags` / env vars (`experiment_flags.py`).

**Metrics.** §13. **Statistics.** §14 [DETAIL REQUIRED after re-runs].

**Hardware.** E1 rows report RTX 3050 6GB. [DETAIL REQUIRED: CPU model, RAM, OS build, Python exact version for camera-ready].

**Software.** `requirements.txt` ranges; optional CuPy in `requirements-gpu.txt`.

---

# 25. Results Skeleton

*Only repository-backed numbers are filled. Empty cells = not yet available.*

| Experiment | Comparison | Metric | Point estimate | CI | Effect size | Figure | Allowed interpretation |
|------------|------------|--------|----------------|----|-------------|--------|------------------------|
| E1 full | — | mean_agency | ≈0.132 | — | — | F4/F5 | Baseline intact circuit metric |
| E1 nopfc | vs full | mean_agency | **0.0** | — | — | F4 | PFC ablation zeroes agency metric |
| E1 nobind | vs full | spike_aligned | **0** | — | — | F4 | Binding required for alignment metric |
| E1 nohippo | vs full | remembered_rate | **0** | — | — | F4 | Hippo required for remembered flag rate |
| E2 | LLM on vs off | trajectories_identical | True (5/5) | — | — | F5 | Headless logged invariance |
| E3 | sleep vs control | mean_recall | ~0.55 vs 0.517 | — | small abs Δ | F6 | Protocol recall improves modestly |
| E4 | selective vs control | emo recall | higher means; advantage mixed | — | — | F6 | Do not claim clean emo selectivity |
| E5 | ground on vs off | seek_food_after_speak | 0.237 vs 0.0 | — | — | F5 | Drive bias; locomotion weak |
| E7 | no_vision vs full | thalamic_world_gain | 0.2 vs 1.0 | — | — | F5 | Mechanism metric; distances unchanged |
| E8 discrim. | aff on vs off | drank_success | true vs false (seeds shown) | — | — | F5 | Compact Arena support for affordances |
| Baselines | NEXO vs reactive/… | survival / goals | — | — | — | — | **EVIDENCE MISSING** |

---

# 26. Discussion Framework

- **Interpretation:** Ablations show selective metric dependence; E2 supports non-decisional language under headless logging; Arena results support bounded causal biases — all within custom protocols.
- **Contribution:** Auditable separation of bias vs commitment is the conceptual center for Adaptive Behavior.
- **Literature:** [DETAIL REQUIRED after DOI verification].
- **Unexpected:** E4 emotion_advantage often ≤0; E5/E7 behavioral distances flat; E1 full zero across-seed variance.
- **Generalization:** Limited to simulated home and implemented metrics.
- **Overinterpretation risks:** “agency” word → free will; LIF counts → brain simulation; HUD guard → formal safety.
- **Future:** Baselines A–J (§12), stats, ecological tasks, physical embodiment **out of scope** unless added.

---

# 27. Limitations

| Limitation | Applies? | Notes |
|------------|----------|-------|
| 2D simplified environment | Yes | |
| Symbolic / summarized sensors | Yes | |
| No physical robot | Yes | |
| Small seed count (n=5; Arena smaller) | Yes | |
| Custom internal metrics | Yes | |
| Missing external baselines | Yes | Critical |
| Strong determinism / identical seeds | Yes | |
| No external public benchmark | Yes | |
| Profile mixing risk | Yes | Document per table |
| Manual parameters / flags | Yes | |
| Ecological validity limited | Yes | |
| Distance from biological neuroscience | Yes | Functional analogs only |
| Reproducibility gaps (license, lockfile, figures) | Yes | |
| Code maturity (research prototype) | Yes | |
| Headless E2 may not invoke live LLM | Yes | Scope claim narrowly |
| Declarative agency_guard ≠ proof | Yes | |

---

# 28. Scientific Claims Risk Register

| Claim | Evidence | Overclaim risk | Safe wording | Required validation |
|-------|----------|----------------|--------------|---------------------|
| Sole choice_key writer is PFC deliberation | code+tests | Medium if “all possible paths” | “Under audited experimental paths…” | Continuous audit + agency-break study |
| Agency / free will | agency metric | **High** | “Internal PFC/limbic ratio metric” | Never equate to phenomenology |
| Consciousness | consciousness flag/module name | **High** | “Optional workspace-inspired module; no subjective claim” | Remove hype language |
| Human brain simulation | scale labels | **High** | “Mesoscale functional analog (≤10,290 active LIF in paper runs)” | Scale honesty table |
| Emotions real | affect vars | **High** | “Affect-like state variables” | |
| AGI / strong autonomy | architecture breadth | **High** | “Research prototype agent” | |
| Language understanding | grounding/LLM | **High** | “String/LLM verbalization and drive bias” | |
| Neurobiological fidelity | LIF equations | **High** | “Simplified LIF populations” | |
| Affordances improve adaptation | Arena JSON | Medium | “In compact Level-2 Arenas tested…” | Multi-seed + baselines |
| Sleep helps memory | E3/E4 | Medium | “Implemented recall score under protocol” | Behavioral probes |

---

# 29. Cover Letter Draft

Dear Editor of *Adaptive Behavior*,

Please consider our manuscript, “Agency-Preserving Action Selection in an Embodied Homeostatic Agent: The NEXO Architecture,” for publication as an Article.

The paper addresses how an artificial agent can adaptively select actions under homeostatic pressure while keeping an auditable boundary between modules that *bias* competition and the module that *commits* a discrete action. We describe the NEXO architecture and report repository-verified ablation, language-invariance, sleep-recall, and causal-affordance Arena results, together with an explicit agenda of missing baselines and statistics.

We believe the work fits the journal’s interest in adaptive and embodied artificial agents. The manuscript is original, not under consideration elsewhere, and involves no human-subjects research. Code and experimental CSV/JSON will be made available upon publication [DETAIL REQUIRED: public repository URL].

Corresponding author: Fernando Andrés Lizana Núñez, Digital Rider SpA, Chile. Email: [DETAIL REQUIRED].

Sincerely,  
Fernando Andrés Lizana Núñez

---

# 30. Declarations Draft

## Author Contributions
F.A.L.N. conceived the architecture, implemented the system, ran experiments, and wrote the manuscript.

## Declaration of Conflicting Interest
The author declares no conflicting interests. [DETAIL REQUIRED if Digital Rider SpA commercial interests apply.]

## Funding
[DETAIL REQUIRED — state “none” if none.]

## Data Availability
Experimental CSV/JSON used in this artifact are in `experiments/results/` of the project repository. [DETAIL REQUIRED: archival DOI/URL.]

## Code Availability
Source code is the `cerebro` / NEXO codebase. [DETAIL REQUIRED: public clone URL + commit hash.]

## Ethical Considerations
Simulation-only; no human or animal subjects.

## Consent to Participate
Not applicable.

## Consent for Publication
Not applicable.

## Acknowledgements
[DETAIL REQUIRED — optional.]

## AI Use Disclosure
Generative AI tools (including Cursor agent models and related assistants) were used for programming assistance, code review, documentation drafting, translation support, and preparation of this publication-audit artifact. The author reviewed all scientific claims against repository evidence and accepts full responsibility for the submitted content. No fabricated experimental results were intentionally introduced; remaining errors are the author’s responsibility.

---

# 31. Author Biography

Fernando Andrés Lizana Núñez is affiliated with Digital Rider SpA, Chile. He develops NEXO (`cerebro`), a research prototype of an embodied, neuro-inspired cognitive architecture for studying homeostatic drives, deliberative action selection, and agency-preserving learning signals in simulated environments. Correspondence: Digital Rider SpA, Chile. [DETAIL REQUIRED: contact email.]

*(≈70 words; no degrees, awards, or publications invented.)*

---

# 32. Submission File Checklist

| File / item | Status now | Needed for submission |
|-------------|------------|------------------------|
| Main manuscript (DOCX/LaTeX per SAGE) | Not generated (MD audit only) | Yes |
| Cover letter | Draft §29 | Yes |
| Figures (high-res) | **MISSING** PNGs | Yes |
| Supplementary material | PARTIAL (`publication_evidence/`) | Recommended |
| Code repository statement | Draft | Yes + public URL |
| Author biography | §31 | Yes |
| Author photograph | **MISSING** | If required by journal |
| COI declaration | Draft | Yes |
| Funding declaration | Placeholder | Yes |
| AI-use declaration | Draft §30 | Yes |
| Data-availability declaration | Draft | Yes |

---

# 33. Reviewer Simulation

### Reviewer 1 — Cognitive architectures  
- **Assessment:** Interesting integrated system; contribution vs ACT-R/Soar unclear without literature and baselines.  
- **Major:** Related work DOIs; novelty vs integration; baseline table.  
- **Minor:** Terminology consistency (E4 vs E8).  
- **Missing experiments:** Architecture-comparable tasks.  
- **Likely reject reasons:** Software demo + custom metrics.  
- **Required for acceptance:** Reframe + baselines + citations.  
- **Recommendation:** **Reject** or **Major Revision** (borderline desk).

### Reviewer 2 — Adaptive behavior / embodied agents  
- **Assessment:** Homeostasis and Arena tasks are on-topic; ecology thin.  
- **Major:** Survival/adaptation metrics; environmental change; n too small.  
- **Minor:** Determinism disclosure.  
- **Missing:** Baselines 1–6; longer horizons.  
- **Recommendation:** **Major Revision**.

### Reviewer 3 — Computational neuroscience / reproducibility  
- **Assessment:** LIF honesty good if exact counts used; “agency” naming risky; stats absent.  
- **Major:** Inferential statistics; lockfile; figure regeneration; avoid brain-equivalence language.  
- **Minor:** Seed variance reporting.  
- **Missing:** Sensitivity on bias caps; GPU/CPU equivalence.  
- **Recommendation:** **Major Revision** (reject if overclaims remain).

---

# 34. Editorial Desk-Rejection Simulation

| Question | Assessment |
|----------|------------|
| In scope? | **Possibly yes** after adaptive-behavior reframing |
| Clear scientific contribution? | **Borderline** — architecture + agency boundary; needs comparative behavior |
| Sufficient experiments? | **No** for Article without baselines/stats |
| Software report risk? | **High** |
| Overclaims? | **Risk medium–high** if older docs leak hype |
| Reproducible methods? | **Partial** |
| Academic English? | Drafts OK with editing |
| References sufficient? | **No** (EVIDENCE MISSING DOIs) |
| Send to review? | **Uncertain — lean no** until Phase 2–3 |

**Estimated probabilities (argumentative, not predictive):** desk rejection **45%**; send to review **35%**; major revision path **15%**; eventual acceptance **5%** *conditional on completing critical experiments*. After major experimental work, desk-reject risk could fall substantially.

---

# 35. Blocking Issues

## Critical Before Submission

| Issue | Impact | Difficulty | Est. time | Files | Closure criterion |
|-------|--------|------------|-----------|-------|-------------------|
| External baselines suite | Desk-reject | High | 3–6 weeks | `experiments/`, new runners | Table T6 filled, n≥20 where feasible |
| Inferential statistics | Credibility | Medium | 1–2 weeks | analysis scripts | CI + tests + effect sizes in manuscript |
| Verified bibliography | Desk-reject | Medium | 1–2 weeks | bib file | Every ref has checked DOI/URL |
| Adaptive Behavior reframing | Fit | Medium | 1 week | manuscript | Lead narrative = adaptation + agency |
| Agency-break control | Supports core claim | Medium | 1–2 weeks | ablation flag + test | Violation metric rises when forced |

## Important Before Submission

| Issue | Impact | Difficulty | Est. time | Closure |
|-------|--------|------------|-----------|---------|
| Multi-seed Arena | Robustness | Medium | 1 week | ≥10 seeds key Arenas |
| Regenerate figures | Production | Low | 1–2 days | PNGs in `publication_evidence/figures/` |
| License + public repo URL | Policy | Low | 1 day | LICENSE + URL in declarations |
| Profile honesty pass | Trust | Low | 2 days | Exact 624/1522/10290 in all tables |
| E4/E5/E7 honest limits | Trust | Low | 2 days | Text states mixed/null behavior effects |

## Desirable Improvements

Lockfile; container; interactive LLM audit; continuous-motor publication table; sensitivity on ±0.08 / 0.10 caps.

## Post-Publication Work

Physical robot; public benchmark port; larger than 10k behavioral studies; formal agency verification tools.

---

# 36. Final Roadmap

| Phase | Tasks | Exit |
|-------|-------|------|
| **1. Evidence consolidation** | Freeze CSV hashes; keep `publication_evidence/`; exact neuron counts; naming E4≠E8 | Inventory complete |
| **2. Missing experiments** | Baselines 1–6; Arena multi-seed; agency-break; optional E5/E7 behavior extensions | New CSVs dated |
| **3. Statistical analysis** | Bootstrap/CI/effect sizes; pre-registered DVs | Analysis notebook + tables |
| **4. Figure generation** | `plot_figures` → controlled folder; F1–F8 designs | Camera-ready PNG/SVG |
| **5. Manuscript drafting** | Titles §19–30; fill DOIs; SAGE formatting | Complete draft |
| **6. Internal review** | Adversarial read vs risk register §28 | Issues closed or deferred explicitly |
| **7. Submission package** | Checklist §32; cover letter; declarations | Submit |

---

# 37. Final Recommendation

## **C. REQUIRES MAJOR EXPERIMENTAL WORK**

**Justification.** NEXO has a clear, code-verified agency boundary (`PrefrontalDeliberation` sole `choice_key` writer), a coherent embodied loop, and non-empty experimental CSVs (E1–E3 at 10,290 LIF; compact E4/E5/E7; Level-2 Arena / E8). That is enough for a **serious preprint / workshop paper**, not yet for a competitive *Adaptive Behavior* Article: missing comparative baselines, inferential statistics, adequate ecological framing, verified references, and production figures. Readiness **42/100** reflects strong architecture/agency documentation offset by weak comparative adaptive-behavior evidence.

**Not A/B:** too many critical gaps. **Not D:** topical fit and verifiable core results exist; the path to submission is experimental and editorial, not a restart.

### Agency finding (summary)

Under audited headless/paper paths, learning and language modules **bias** Go/drives/sensory evidence only; **`PrefrontalDeliberation.run` alone assigns `choice_key`**. `agency_guard` in `causal_hud.py` is declarative documentation, not a formal proof. An agency-break ablation remains **EVIDENCE MISSING**.

---

## Appendix A — Primary evidence paths

- Code: `brain/deliberation.py`, `experiment_flags.py`, `affordance_map.py`, `td_reward.py`, `grounding.py`, `agent_loop.py`, `mind.py`, `body.py`, `profile.py`, `causal_hud.py`, `sleep_architecture.py`, `language_cortex.py`
- Results: `experiments/results/e1_*`, `e2_llm_invariance.csv`, `e3_sleep_recall.csv`, `e4_sleep_selective.csv`, `e5_grounding.csv`, `e7_multimodal.csv`, `arena_*.json`
- Package: `publication_evidence/README.md`, `evidence_inventory.csv`, `missing_experiments.md`, `reproduction_commands.md`

## Appendix B — Status tag legend

| Tag | Meaning |
|-----|---------|
| VERIFIED | Confirmed in code, test, and/or CSV/JSON this audit |
| PARTIALLY VERIFIED | Evidence exists but incomplete, mixed, or protocol-limited |
| PROPOSED | Planned design / wording; not claimed as result |
| NOT YET TESTED | Implementable but no publication table |
| EVIDENCE MISSING | Required claim/support absent from repository |
