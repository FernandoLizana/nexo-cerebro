# P7 — Resume and Checkpoint

State persisted to `population_state.json`:

- `PopulationState.records` — per-run `RunExecutionRecord`
- Checkpoint written after each run completes
- `resume=True` — reloads state, skips `COMPLETED` runs
- `pending_run_ids()` — only `PLANNED`, `QUEUED`, `FAILED_INFRASTRUCTURE`
- Re-running resume is **idempotent** — no duplicate completed runs

CLI: `python -m nexo_qa.population.cli run <config> --resume`
