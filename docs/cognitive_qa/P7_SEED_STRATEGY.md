# P7 — Seed Strategy

Child seeds are **hash-derived** and **reordering-invariant**:

```python
derive_child_seed(master_seed, cohort_id, task_id, sample_index, persona_id, condition_set_id)
derive_run_id(spec_hash, cohort_id, task_id, persona_id, seed, condition_set_id, sample_index)
```

Changing execution parallelism or run order **does not** change seeds or run IDs.

Implementation: `nexo_qa/population/seeds.py`
