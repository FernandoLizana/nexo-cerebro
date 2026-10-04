# P5 — Handoff to P6

## P6 Mission

Cognitive QA Metrics + Failure Taxonomy + Cognitive Failure Certificate

## Data P5 provides

```text
persona_id
traits (immutable)
persona_state (frustration, fatigue, …)
actions / action_salience
goal / goal_progress
percepts / attention traces
errors / policy blocks
behavioral fingerprint
paired run metadata
```

## Artifacts for P6

- `artifacts/p5/quality_gate.json`
- `artifacts/p5/paired_runs.json`
- `artifacts/p5/sensitivity_analysis.json`
- `artifacts/p5/behavioral_fingerprints.json`

## Do not start P6 without

1. Reading `docs/entregas/P5_NEXO_COGNITIVE_QA_ENTREGA.md`
2. Confirming `bind_persona()` opt-in boundary
3. Preserving v90 golden

## Metrics deferred from P5

NCFS, HFP, CRS — commercial KPIs belong to P6.
