# P7 — Cognitive Stress Testing

`CognitiveStressTest` + `wm_sweep()` generate one-factor-at-a-time population specs:

- Each axis level → separate cohort
- Constant task + seeds per cell; vary one P5 trait
- `manifest()` documents planned cells and run count
- Config: `configs/nexo_qa/populations/wm_stress_population.yaml`

Stress curves and breakpoint detection are manifest-level in P7; full sweeps run offline or in dedicated CI jobs.
