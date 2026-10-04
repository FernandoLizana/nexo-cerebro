# P0 — V90 config baseline

**File:** `configs/nexo/integrated_v90.yaml`  
**Loaded by:** `nexo.integrated_runtime.runtime_from_config` (`nexo/integrated_runtime.py`)  
**P0 rule:** values were **not** changed.

Unknown YAML keys are ignored (`data.get(...)`). A `cognitive_qa:` block was **not** added to this file so historical hashes/profiles stay byte-stable.

## Identity

| Key | Value |
|-----|-------|
| `profile` | `integrated_v90` |
| `seed` | `42` |
| `ticks` | `120` (CLI/CI often override with `--ticks 12`) |
| `connectome` | `configs/connectome/connectome_v1.yaml` |
| `telemetry_level` | `summary` |
| `lesion_profile` | `lesion_none` |
| `use_legacy_adapter` | `true` |
| `disable_processes` | `[]` |
| `legacy_advisory_weight` | `0.6` |
| `deliberation_unified_mode` | `legacy` (skipped when weight mode is integrated) |

## Cognitive / body flags (all `integrated` unless noted)

| Flag | Value | Runtime effect |
|------|-------|----------------|
| `body_enabled` | `true` | `VirtualBody` + metabolism/interoception/allostasis |
| `perception_mode` | `predictive` | raw capture + thalamus + hierarchy + predictive attention |
| `memory_mode` | `integrated` | enhanced WM + hippocampal encode/retrieve |
| `executive_mode` | `integrated` | goal stack + PFC + enhanced BG + cerebellum |
| `learning_mode` | `integrated` | TD bias/learn + neuromodulators + plasticity |
| `consciousness_mode` | `integrated` | global workspace + metacognition |
| `social_mode` | `integrated` | ToM + social exchange + language |
| `sleep_mode` | `integrated` | sleep architecture + replay + consolidation + development |
| `world_mode` | `world_demo_facade` | `WorldDemoFacade` over legacy `brain.world` |
| `unified_motor_mode` | `integrated` | audit event `unified.motor`; still executes via `MotorExecutionProcess` |
| `causal_certificate_mode` | `integrated` | `CausalCertificateProcess` every tick (priority 50) |
| `agency_audit_mode` | `integrated` | `AgencyAuditProcess` every 4 ticks (priority 49) |
| `memory_unification_mode` | `integrated` | hippo → SQLite after consolidation |
| `day_in_the_life_mode` | `integrated` | `clock.seconds_per_tick` from YAML (`300.0`, 288 ticks in nested block) |
| `science_bundle_mode` | `integrated` | export envelope H1+H2 after `nexo.run` |

World/demo compatibility also `integrated`: `world2d_headless_mode`, `world2d_legacy_actions_mode`, `world2d_full_actions_mode`, `world2d_legacy_env_mode`, `flask_unified_mode`, `agent_loop_sync_mode`, `memory_bridge_mode`, `roadmap100_*`, `autonomy_guard_mode`, `hypothalamus_multimodal_mode`, `companion_integrated_mode`.

Science/export cluster also `integrated`: tracing, replication, permutation, correction, eventlog, meta_analysis, cross_battery, phenomenology, inference, hierarchical_inference, orchestration, scale, publication, paper_pack, battery_paper, paper_figures, pipeline_paper, latex_master, battery_full, release_bundle, full_publication, gpu_bench, lif_scale.

## Nested blocks (export paths only; P0 did not execute the full paper pipeline)

See YAML keys `tracing`, `replication`, `correction`, `meta_analysis`, `cross_battery`, `agency_audit`, `science_bundle`, `causal_certificate`, `day_in_the_life`, `battery.manifest` → `configs/battery/integrated_v19.yaml`.

`pipeline_paper.auto_run: true` with `integrated_v19_mini.yaml` — **not** invoked by P0 golden runs (those call `IntegratedRuntime.run(ticks=12)` directly).

## How to detect accidental Cognitive QA drift

Compare a later run against `artifacts/baseline/p0/reproducibility/run_A.json`:

- `trajectory_hash` (STRICT)
- `actions_taken`
- `metrics.mean_reward`, `final_energy`
- `causal.valid_certificates`, `agency.agency_score`
