# P0 — Reproducibility baseline

**Scenario:** `configs/nexo/integrated_v90.yaml` via `runtime_from_config` + `IntegratedRuntime.run(ticks=12)`  
**Seed:** 42 (YAML)  
**Env:** `NEXO_SKIP_GPU_BENCH=1`  
**Why this run:** same as CI smoke (`nexo.run --ticks 12`) but **without** the YAML paper/export pipeline, so the comparison is the cognitive loop rather than file timestamps.

Artifacts: `artifacts/baseline/p0/reproducibility/run_A.json`, `run_B.json`, `comparison.json`.

## STRICT invariants (must be identical)

| Check | Run A | Run B | Equal |
|-------|-------|-------|-------|
| no crash | true | true | yes |
| ticks | 12 | 12 | yes |
| `trajectory_hash` | `77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c` | same | **yes** |
| `actions_taken` | 12× `explore` | same | **yes** |
| certificates generated | `valid_certificates=12` | 12 | yes |
| `agency_score` | 1.0 | 1.0 | yes |

## STATISTICAL invariants (identical on this machine)

| Metric | A | B |
|--------|---|---|
| `mean_reward` | 0.12 | 0.12 |
| `final_energy` | 0.3526710863756767 | same |
| `eat_ratio` | 0.0 | 0.0 |
| `event_count` | 421 | 421 |

Entropy near 0 because a single action (`explore`) dominates. This is **v90 facade behavior**, not a failed test.

## INFORMATIONAL (may vary)

| Item | Notes |
|------|-------|
| wall time | A 3.688 s, B 3.442 s (startup included) |
| ticks/sec | ~3.25–3.49 |
| `encoded_memory` ids | `RoomWorld.apply_action` uses `uuid4()` — **not** a STRICT invariant |
| RAM/CPU | not sampled (`psutil` not a direct dependency) |

## What must stay identical vs what may vary later

- **Identical:** action sequence / `trajectory_hash`, certificate count, energy after 12 ticks, mean reward.
- **May vary:** elapsed time, UUID episode ids, any export JSON timestamps if using full `nexo.run` paper pipeline.

## Event/tracing coverage (v90 this run)

See `run_A.json` `event_type_counts`.

| Element | Disponible | Parcial | Ausente |
|---------|------------|---------|---------|
| Estado previo | | X (CognitiveState, no snapshot de world flags) | |
| Percepción | X `perception.updated` | | |
| Acción disponible | | X in `action.selected.candidates` | |
| Acción elegida | X `action.selected` | | |
| Utilidad | | X scores/confidence | |
| Resultado | | X slices only | |
| Reward | X `reward.received` | | |
| Memoria | | X encode/retrieve | |
| Estado posterior | | X next-tick percepts | |
| Certificado causal | X `causal.certificate` (mode on) | | |
