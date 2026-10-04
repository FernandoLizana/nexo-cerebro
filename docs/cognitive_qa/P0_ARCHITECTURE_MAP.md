# P0 — Architecture map

**Inventory reuse:** `python -m scripts.generate_repository_inventory` → `reports/repository_inventory.json` (605 pytest collected, git `3a0233c3…`, dirty workspace from `data/brain_state/*` runtime files).

Copy for P0: `artifacts/baseline/p0/repository_inventory.json`.

## Entry points

| Path | Role | Tag |
|------|------|-----|
| `nexo/run.py` `main` | CLI YAML → `runtime_from_config` | INFRASTRUCTURE |
| `app.py` | Flask demo + optional `FlaskUnifiedSession` | DEMO |
| `experiments/integrated_battery/run_manifest.py` | Battery YAML | EXPERIMENTATION |
| `experiments/personal/run_h1_*.py`, `run_h2_agency_audit.py` | Personal science | EXPERIMENTATION |
| `experiments/run_all.py` | Legacy paper E1–E3 | EXPERIMENTATION |

## Dual stack

```text
brain/ (128 py)     InfantApeBrain + NeuralAgentLoop + World2D     LEGACY CORE
nexo/  (194 py)     IntegratedRuntime + CognitiveScheduler         INTEGRATED CORE
nexo_qa/ (P0)       empty extension namespace                      QA SKELETON
```

## nexo packages (classification)

| Package | Tag | Responsabilidad |
|---------|-----|-----------------|
| `nexo/core/` | CORE | scheduler, clock, events, state_store, process_* |
| `nexo/connectome/` | CORE | graph YAML, routing, latency, plasticity |
| `nexo/perception/`, `nexo/thalamus/` | PERCEPTION / ATTENTION | predictive coding, TRN |
| `nexo/memory/`, `nexo/working_memory/` | MEMORY | hipocampo + WM |
| `nexo/prefrontal/`, `nexo/planning/`, `nexo/basal_ganglia/` | DECISION | PFC, goals, Go/No-Go |
| `nexo/cerebellum/` | MOTOR | smoothing |
| `nexo/body/`, `nexo/homeostasis/` | BODY | energía, drives, allostasis |
| `nexo/reinforcement/` | REWARD | TD |
| `nexo/neuromodulation/` | AFFECT | moduladores |
| `nexo/workspace/`, `nexo/metacognition/` | ATTENTION / METACOGNITION | GWT, duda |
| `nexo/sleep/`, `nexo/development/` | SLEEP / LEARNING | fases + maduración |
| `nexo/social/`, `nexo/language/` | SOCIAL | ToM, utterances |
| `nexo/demo/` | ENVIRONMENT / DEMO | worlds + Flask bridges |
| `nexo/behavioral/` | BEHAVIORAL / STATISTICS / REPLICATION / PUBLICATION | tasks, FDR, paper, certificates |
| `nexo/ablation/`, `nexo/interventions/` | EXPERIMENTATION | ablaciones, lesiones |
| `nexo/telemetry/` | INFRASTRUCTURE | traces |
| `nexo/decision_audit.py`, `agency_metrics.py` | AGENCY | AST + proxies |
| `nexo/environment.py` | REPLICATION | snapshot de máquina (nombre confuso) |
| `nexo/behavioral_tasks.py` | LEGACY | 2 tasks InfantApeBrain |

## Scheduler priorities (v90 relevant)

See `CognitiveScheduler.step` — higher priority first. Motor execute = **55**. Causal certificate = **50**. Agency audit = **49**.

Full table in conversation audit; critical order for QA: perceive (92–87) → body (86–75) → decide (71–60) → motor (55) → learn/memory (54–52) → certificate/audit (50–49).

## Worlds

`create_world` modes: `room` (default RoomWorld), `extended`, `world_demo_facade` (**v90**), `world3d_sync`, `world2d_headless`, `world2d_legacy_env`, `world2d_lite`.

## Tests / configs / scripts

- `tests/` 93 python files, 605 collected (pytest `norecursedirs` excludes artifacts/publication packs).
- `configs/nexo/integrated_v90.yaml` profile máximo.
- Reused scripts: `generate_repository_inventory.py`, `check_dependency_consistency.py`, `verify_artifact.py`, `validate_roadmap_traceability.py`. P0 did **not** duplicate them.

## UNKNOWN (kept)

`brain/archetype_cards.py`, `brain/journey.py` — symbolic demo content. Not deleted.

## Future reserved layout (NOT created in P0)

```text
nexo_qa/
├── browser/
├── perception/
├── actions/
├── goals/
├── personas/
├── scenarios/
├── population/
├── metrics/
├── reports/
├── validation/
└── observability/
```

Only `nexo_qa/__init__.py` exists.
