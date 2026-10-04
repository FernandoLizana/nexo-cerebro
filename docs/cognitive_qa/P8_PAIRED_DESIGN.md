# P8 — Paired Design

Each perturbation generates a **pair**:

- `pair_id` links baseline + perturbed runs
- Same `task_id`, `persona_id`, `seed` (via `derive_paired_seed`)
- Only `condition_set_id` / perturbation differs
- Invalid pairs excluded with explicit denominator

`validate_pair_invariants()` · `compute_paired_delta()` in `nexo_qa/chaos/pairs.py`
