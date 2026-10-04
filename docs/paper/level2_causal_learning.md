# Level 2 — Minimal causal learning (paper note)

**Status:** implemented in code (V2.5). Compact Arena results are the primary evidence for this claim; E1–E3 remain the 10k ablation/LLM/sleep tables. Paper experiment ID: **E8** (E4 already = selective sleep).

## Claim

Nexo can learn `object + interaction + dominant drive → observed body change` and reuse that evidence as **bounded bias** (±0.08) and **navigation prior**, without ever writing `choice_key` outside `PrefrontalDeliberation.run`.

## Agency invariants

| Module | Writes `choice_key`? |
|--------|----------------------|
| AffordanceMap | No |
| CounterfactualSimulator | No |
| SchemaLearner (`learned_aff_*`) | No (menu only) |
| Causal HUD / telemetry | No |
| PrefrontalDeliberation | **Yes (sole writer)** |
| LLM / Ollama | No (post-hoc) |

## Mechanisms (code)

- `brain/affordance_map.py` — observe, confidence, sleep prune
- `brain/counterfactual_simulator.py` — bias ≤ ±0.06
- `brain/learned_schemas.py` — `note_affordance_success`
- `brain/agent_loop.py` — navigation prior by successful `object_id`; type transfer if instance gone
- `world.dry_object_ids` — per-instance dry fountains for discrimination

## Arena protocol (compact)

```bash
python -m experiments.run_arena_thirst --seeds 3 --profile compact
python -m experiments.run_arena_extra --seeds 2 --profile compact
python -m experiments.run_arena_level24 --seeds 2 --profile compact
python -m experiments.run_arena_level25 --seeds 2 --profile compact
```

| Task | aff_on (typical) | aff_off (typical) |
|------|------------------|-------------------|
| thirst exp.2 | success, ~16 ticks | timeout |
| hunger exp.2 | success, ~11 ticks | timeout |
| transfer A→B | drinks at B (~27 ticks) | fails |
| discrimination | goal = good; drinks (~22 ticks compact; ~14 ticks 10k smoke) | nearer dry / no relief |
| hygiene exp.2 | success, ~11 ticks | timeout |
| dry fountain | failures recorded, gain≈0 | — |

10k smoke (1 seed): `experiments/results/arena_10k/arena_discrimination.json` — aff_on drank=True ticks=14; aff_off timeout.

Exact CSVs/JSON: `experiments/results/arena_*.json` after runners. Figure: `experiments/figures/fig9_e8_causal_arena.png`.

## Demo

```bash
set CEREBRO_DEMO_LITE=1
set CEREBRO_AFFORDANCES=1
set CEREBRO_COUNTERFACTUAL=1
set CEREBRO_TELEMETRY=1
python app.py
# UI: panel «Decisión causal»; API: GET /api/neural/causal/hud
```

CI smoke without leaving the server up: `pytest tests/test_demo_hud.py`.

## Relation to paper tables

- **Do not** replace E1–E3 10k numbers with Arena compact ticks.
- Cite Level 2 / **E8** as an additional mechanism + ecological Arena evidence.
- Optional future work: re-run E8 under `--profile 10k` with multiple seeds.
- Full manuscripts: [`paper_causal_affordances.md`](paper_causal_affordances.md) (ES), [`draft_causal_affordances_en.md`](draft_causal_affordances_en.md) (EN).
