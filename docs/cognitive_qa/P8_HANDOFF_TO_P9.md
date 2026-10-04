# P8 — Handoff to P9

P9 (Human Calibration Lab) receives reproducible datasets:

- Baseline + perturbed runs with paired deltas
- Personas, conditions, metrics, certificates
- Cohort sensitivity matrices

Entry:

```python
from nexo_qa.chaos import ChaosRunner, analyze_chaos_directory
```

Artifacts: `artifacts/p8/chaos/<chaos_id>/`
