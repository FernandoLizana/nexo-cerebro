# P7 — Overview

P7 adds a **Population Engine** on top of P6 single-run Cognitive QA:

```text
PopulationSpec → Planner → RunPlan[] → Runner → P6 per run → Aggregator → Report
```

**Module:** `nexo_qa/population/`  
**Phase:** P7 · **Version:** `0.7.0-p7`

Key capabilities: deterministic run plans, dry-run, run-count guards, bounded parallelism, resume/checkpoint, cohort aggregation, failure clustering, cognitive stress manifests, JSON/Markdown/CSV reporting.

**Disclaimer:** All population metrics are **simulation distributions**, not human population estimates.
