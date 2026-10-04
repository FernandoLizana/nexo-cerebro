# Missing Experiments — Adaptive Behavior Submission Gap List

Status legend: **MISSING** = not run / not in repo; **PARTIAL** = smoke or n small; **DONE** = CSV/JSON present (still may need more seeds/stats).

## Critical (block Adaptive Behavior Article)

| ID | Experiment | Why required | Current status | Suggested design |
|----|------------|--------------|----------------|------------------|
| M1 | External baselines (rule reactive, no-memory, no-homeostasis, no-deliberation, TD-direct policy, full NEXO) | Journal expects comparative adaptive behavior | **MISSING** | Same 2D home; 20–30 seeds; survival + homeostatic deviation + goal completion |
| M2 | Inferential statistics on E1–E3 / Arena | Means without CI/tests are insufficient | **MISSING** | Bootstrap CIs; Wilcoxon / permutation; effect sizes; multiple-comparison correction |
| M3 | Seed power ≥20 where feasible | Current n=5 (Arena often n=1–2); E1 full often zero across-seed variance | **PARTIAL** | Re-run compact for power; 10k for key arms only |
| M4 | Ecological / open-ended adaptation tasks | Adaptive Behavior focus | **PARTIAL** (Arena thirst/hunger/hygiene) | Longer horizons; environment shifts; transfer metrics |
| M5 | Agency-break control (allow module to write `choice_key`) | Need causal evidence of boundary value | **MISSING** (only design docs + unit tests that boundary holds) | Ablation: grounding/LLM/TD force action; measure coherence + audit violations |
| M6 | External benchmark or published task suite | Avoid software-demo desk reject | **MISSING** | Map to a public grid/homeostasis / MiniGrid-like suite **or** fully specify custom protocol + release |

## Important

| ID | Experiment | Status | Notes |
|----|------------|--------|-------|
| M7 | E1–E3 on compact **and** 10k with identical protocol statement | **PARTIAL** | E1–E3 CSV are 10k; E4/E5/E7 compact — do not mix in one table |
| M8 | Arena Level 2 multi-seed (discrimination, transfer, hunger, hygiene) | **PARTIAL** | Some JSON show seed 0 only / small N |
| M9 | Selective sleep E4 emotional advantage analysis | **PARTIAL** | CSV exists; advantage often ~0 or inconsistent — needs honest stats |
| M10 | Grounding E5 behavioral approach (distance/near ticks) | **PARTIAL** | `seek_food_after_speak` rises ON; distance deltas tiny; high determinism |
| M11 | Multimodal E7 behavioral effect beyond thalamic gain | **PARTIAL** | Distances identical full vs no_vision in CSV — mechanism metric only |
| M12 | Continuous-motor / navigation bias audit under headless | **NOT YET TESTED** as publication table | Can bias locomotion without writing `choice_key` |
| M13 | Figure regeneration (fig1–fig9) into controlled folder | **EVIDENCE MISSING** (PNGs absent at audit) | `python -m experiments.plot_figures` → save under `publication_evidence/figures/` |

## Desirable

| ID | Item | Status |
|----|------|--------|
| M14 | Sensitivity analysis on Go bias caps (±0.08 affordance, TD bound) | **PROPOSED** |
| M15 | GPU vs CPU equivalence report for E1 | **PARTIAL** (hardware noted in CSV) |
| M16 | Container / lockfile (`requirements.lock`) | **MISSING** (only `requirements.txt` ranges) |
| M17 | Human-readable survival episodes for Adaptive Behavior narrative | **PROPOSED** |

## Obtained vs still needed (summary)

**Obtained (repo):** E1 ablations (10k, 5 seeds), E2 LLM invariance (5 seeds), E3 sleep recall (5 seeds), E4 selective sleep (compact), E5 grounding (compact), E7 multimodal gain (compact), Arena affordance tasks (compact; E8 naming), agency unit tests, tick bench CSV.

**Still needed for Adaptive Behavior Article:** baselines, stats, larger N, ecological framing tables, agency-break control, regenerated figures, verified bibliography with DOIs.
