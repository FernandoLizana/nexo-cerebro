# Nexo: Spike-Gated Embodied Autonomy through Prefrontal–Limbic Deliberation without LLM Planning

**Workshop draft (6–8 pages)** — arquitectura cognitiva mesoescala con ablaciones reproducibles.

---

## Abstract

Large language models dominate conversational agents, but their planning loop is opaque and decoupled from embodiment. We present **Nexo**, a neuro-inspired cognitive architecture with **configurable mesoscale profiles** (~500 to ~10.3k active LIF neurons) where homeostatic drives, prefrontal–limbic competition, and spike-gated basal ganglia select actions in a 2D home environment. An optional LLM layer (Ollama) articulates internal state via Broca/Wernicke analogs but does **not** participate in motor or deliberation decisions. We report ablation studies (intention binding, PFC, hippocampus, affect), LLM invariance of motor trajectories, sleep-dependent recall, and **minimal causal affordance learning** (Level 2 Arena) that biases PFC without writing `choice_key`. **Published E1–E3 results use `SCALE_10K_PROFILE` (~10,290 neurons);** Arena Level 2 smoke uses `COMPACT_PROFILE`.

---

## 1. Introduction

Embodied cognitive agents must balance visceral drives, learned habits, and contextual prediction without outsourcing control to an external planner. Classical cognitive architectures (ACT-R, Leabra) emphasize modular memory and production rules; recent LLM agents collapse perception, memory, and action into a single text channel.

Nexo takes a middle path: **spiking cortical columns**, hippocampal episodic memory, and explicit prefrontal deliberation produce motor indices; language is a read-out. Contributions:

1. Integrated body–brain–world loop with homeostatic drives and neuromodulators.
2. An **intention circuit** linking deliberation → sensory priming → spike alignment → PFC motor veto.
3. Scalable episodic memory via disk-indexed virtual assemblies.
4. **Causal affordances** (object + interaction → body delta) with agency invariants.

---

## 2. Architecture

See `docs/paper/architecture.md` and [`perfiles_y_experimentos.md`](perfiles_y_experimentos.md). Causal detail: [`level2_causal_learning.md`](level2_causal_learning.md).

**Perception.** Thalamic relay fuses world, vision, and olfactory vectors into sensory cortex.

**Deliberation.** `PrefrontalDeliberation` runs Go/No-Go competition (limbic vs PFC) with GABA inhibition and dopaminergic gain. **Only here** is `choice_key` written.

**Causal layer (Level 2).** `AffordanceMap` observes homeostatic outcomes (±0.08 bias). Counterfactual simulator (±0.06). Optional `learned_aff_*` schemas expand the menu. HUD/telemetry are read-only.

**Intention / memory / language.** Spike-gated basal ganglia; DG–CA3–CA1 + sleep consolidation; Ollama post-hoc only (E2).

---

## 3. Mechanisms

### 3.1–3.3 Deliberation, spike gating, plasticity

As in prior drafts: continuous Go/No-Go, spike-aligned motor, STDP + hippocampal pattern completion.

### 3.4 Minimal causal learning

`objeto + interacción + drive → Δcuerpo`. Failures (dry fountain) accumulate negative evidence; successes guide navigation by `object_id` (discrimination) or by type when the instance disappears (transfer). Sleep reinforces reliable records and prunes chronic failures.

---

## 4. Experiments

**E1–E3 (paper tables):** `SCALE_10K_PROFILE`, headless, 5 seeds, `CEREBRO_OLLAMA=0` unless E2.

| Exp | Question |
|-----|----------|
| E1 | Ablations (NoBind, NoPFC, NoHippo, NoAffect) |
| E2 | LLM invariance of trajectories |
| E3 | Sleep vs control recall |

**E8 — Causal Arena (Level 2):** compact smoke (and optional 10k). Agency violations = 0.

| Task | Prediction |
|------|------------|
| thirst / hunger / hygiene | aff_on returns; aff_off timeout |
| transfer A→B | type generalization after A removed |
| discrimination good vs dry | prefer successful `object_id` over nearer dry |

Runners: `run_arena_thirst`, `run_arena_extra`, `run_arena_level24`, `run_arena_level25`.

---

## 5. Related work

ACT-R, Leabra, Spaun/Nengo, LLM agents (ReAct), predictive processing — as prior draft. Level 2 relates to affordance learning and model-based bias without replacing PFC selection.

---

## 6. Discussion

**Limits.** Mesoscale only; Arena may use fast locomotion for budgets (physics smoke exists); E4 compact ≠ E1–E3 10k tables.

**Strengths.** Reproducible ablations, explicit LLM separation, causal learning with agency guards, open Python implementation.

**Future.** Peer-reviewed benchmarks; optional E4 at 10k; richer multi-object curricula.

---

## 7. Reproducibility

```bash
pip install -r requirements.txt
python -m experiments.run_all --profile 10k --seeds 5 --steps 200 --workers 2
python -m experiments.run_all --profile compact --seeds 2 --steps 30
python -m experiments.run_arena_level25 --seeds 2 --profile compact
```

Demo HUD (no long server needed for CI): `tests/test_demo_hud.py` via Flask test client.

---

## References (selected)

- Anderson, J. R., et al. (2004). An integrated theory of the mind. *Psychological Review*.
- O’Reilly, R. C., & Munakata, Y. (2000). *Computational Explorations in Cognitive Neuroscience*.
- Eliasmith, C., et al. (2012). A large-scale model of the functioning brain. *Science*.
- Yao, S., et al. (2023). ReAct: Synergizing reasoning and acting in language models.

---

*Workshop draft; Level 2 causal section 2026-07. E1–E3 figures from `experiments/run_all.py`.*
