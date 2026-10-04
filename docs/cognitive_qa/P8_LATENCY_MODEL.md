# P8 — Latency Model

`LATENCY` delays action acceptance for N ticks with observable `loading_spinner` percept.

Levels configured via `parameters.delay_ticks` — not raw sleep without perceptual effect.

Measures impact via P6 metrics (NCFS, stagnation, repeated actions) — not duplicated in P8.
