# P5 — Behavioral Diversity

## Principle

Differences must emerge from WM, attention, risk, fatigue, frustration — not scripted errors.

## Paired Experiment

```text
task: risky_confirmation.html
seed: 42
persona A: risk_averse
persona B: impatient
```

Observed: distinct `persona_modifiers`; action traces may differ by scenario sensitivity.

## Fingerprint

Reuses `nexo.behavioral.fingerprint.compute_behavior_fingerprint` via `nexo_qa/personas/runner.py`.

## Matrix Runner

```python
run_matrix(task_id=..., personas=(...), seeds=(...), ticks=..., setup=..., teardown=...)
```

Small matrices only — full population engine is P7.

## Outputs per run

actions, ticks, frustration_end, fatigue_end, progress, fingerprint

See `artifacts/p5/paired_runs.json`
