# P7 — Run Plan

`PopulationPlanner.plan()` produces a complete `RunPlan[]` **before** execution:

Each `RunPlan` includes: `run_id`, `seed`, `persona_id`, `cohort_id`, `task_id`, `condition_set_id`, `config_versions`, `artifact_path`.

Plans are sorted by `run_id` for stable `plan_hash()`.

Dry-run: `PopulationPlanner.dry_run_report()` — estimated runs vs budget, no browser.

CLI: `python -m nexo_qa.population.cli plan configs/nexo_qa/populations/baseline_population.yaml --dry-run`
