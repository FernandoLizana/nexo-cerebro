# P7 — Handoff to P8

P8 (Cognitive Chaos Testing) receives:

- `PopulationSpec` + `ConditionSet` (e.g. `BASELINE` vs `INTERRUPTED`)
- Paired seeds (same persona + seed + task across conditions)
- `PopulationRunner` + `PopulationAggregator`
- P6 single-run metrics unchanged

P8 adds environmental perturbations (latency, interruptions, error injection) as condition dimensions on the same infrastructure.

Entry point:

```python
from nexo_qa.population import PopulationPlanner, PopulationRunner, PopulationSpec
```

Configs: `configs/nexo_qa/populations/`
