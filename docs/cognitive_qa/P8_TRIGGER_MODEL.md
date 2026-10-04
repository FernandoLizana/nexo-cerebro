# P8 — Trigger Model

Deterministic triggers preferred (`nexo_qa/chaos/triggers.py`):

- `AT_TICK` — fire at tick N
- `AFTER_ACTION` — after N actions
- `ON_PAGE`, `ON_GOAL_PROGRESS`, `AFTER_DURATION`
- `PROBABILISTIC_SEEDED` — hash-based, reproducible

Events: `PERTURBATION_SCHEDULED`, `STARTED`, `UPDATED`, `ENDED`, `INJECTION_FAILURE`

No oracle triggers based on “correct next action”.
