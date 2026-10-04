# Minimal Causal Affordance Learning under Prefrontal Sovereignty in an Embodied Agent

**Short workshop draft (EN)** · Companion to the full Spanish manuscript [`paper_causal_affordances.md`](paper_causal_affordances.md).  
**System:** Nexo · **Main experiment:** E8 Level-2 Arena · **Authors:** see [`AUTHORS.template.md`](AUTHORS.template.md)

---

## Abstract

LLM agents often conflate language with action selection. In **Nexo**, only prefrontal deliberation writes `choice_key`; speech is post-hoc. We add a **minimal causal affordance** layer: after each real interaction, the agent records homeostatic body change (`object + interaction + drive → Δbody`) and feeds bounded Go evidence (±0.08) plus a navigation prior—never forcing motor output. Arena tasks (novel water/food/hygiene, type transfer, good-vs-dry discrimination) show return-after-exposure and instance discrimination when learning is on, and timeout when off, with zero agency violations. Primary results use a compact ~500-LIF profile; a 10k smoke replicates discrimination.

**Keywords:** affordances; embodied autonomy; prefrontal deliberation; causal learning; non-decisional LLM.

---

## 1. Introduction

Embodied autonomy requires homeostasis, memory, and action without opaque language-as-policy. We ask whether an agent can learn interaction consequences while preserving an explicit **agency contract**: modules may bias, only PFC selects.

**Contributions.** (1) Persistent AffordanceMap with clamped bias; (2) optional counterfactuals (±0.06) and `learned_aff_*` menu entries; (3) reproducible E8 Arenas; (4) empirical compact results + 10k smoke. Ablation/LLM/sleep results (E1–E3) appear in a sibling paper and are not replaced here.

---

## 2. Method (sketch)

Interaction → body snapshot before/after → AffordanceMap.observe → evidence for existing PFC contestants. Navigation prefers successful `object_id` when present; falls back to nearest same-type instance if the learned id is gone (transfer). Dry instances are marked per-id (`dry_object_ids`).

Agency table: AffordanceMap / CF / schemas / HUD / LLM never write `choice_key`; `PrefrontalDeliberation.run` is the sole writer.

---

## 3. Experiments (E8)

| Task | aff_on (compact) | aff_off |
|------|------------------|---------|
| Thirst / hunger / hygiene return | success | timeout |
| Transfer A→B | drinks at B | fail |
| Discrimination good vs dry | ~22 ticks, goal=good | timeout near dry |

Figure: `experiments/figures/fig9_e8_causal_arena.png`.  
10k smoke (1 seed): aff_on **14** ticks success; aff_off timeout.

```bash
python -m experiments.run_arena_level25 --seeds 2 --profile compact
```

---

## 4. Discussion

E8 supports return, transfer, and discrimination under bounded evidence without turning affordances into a planner. Limits: custom metrics, compact primary scale, optional fast locomotion in Arena, strong determinism. Future: multi-seed 10k E8; CLEI PDF after author metadata.

---

## References (selected)

Gibson (1979); Anderson et al. (2004); O’Reilly & Munakata (2000); Yao et al. (2023). Full list and Spanish prose: [`paper_causal_affordances.md`](paper_causal_affordances.md).

---

*EN short draft · July 2026 · Authors TODO*
