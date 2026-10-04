# REPRODUCTION_README — NEXO Adaptive Behavior package

Author: Fernando Andrés Lizana Núñez / Digital Rider SpA / Chile  
ORCID / funding: **AUTHOR TO CONFIRM** (none invented here).

## Requirements

- Python 3.11+ (locked freeze in `requirements-lock.txt` when generated from `.venv`)
- Windows PowerShell or bash
- Do **not** need secrets, Ollama, or private DB for these headless runs

```powershell
cd <repo-root>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# optional GPU:
# pip install -r requirements-gpu.txt
```

## One-shot (PowerShell)

```powershell
.\publication_finalization\reproduce_all.ps1
```

## One-shot (bash)

```bash
bash publication_finalization/reproduce_all.sh
```

## Manual steps

1. Read `COMPUTE_ESTIMATE.md` (policy: compact primary).
2. Run experiments:

```powershell
$env:CEREBRO_OLLAMA="0"
$env:CEREBRO_SKIP_PROCESS_GUARD="1"
.\.venv\Scripts\python.exe -u publication_finalization\scripts\run_publication_experiments.py --phase all --seeds 10 --steps 100 --profile compact
```

3. Motor audit:

```powershell
.\.venv\Scripts\python.exe -u publication_finalization\scripts\run_motor_audit.py
```

4. Stats:

```powershell
.\.venv\Scripts\python.exe -u publication_finalization\scripts\build_stats.py
```

5. Figures:

```powershell
.\.venv\Scripts\python.exe -u publication_finalization\figure_scripts\plot_publication_figures.py
```

## Honesty constraints

- Historical E1–E3 remain n=5 @10k; new baselines are compact n=10.
- Do not mix profiles in one primary table without labels.
- Study wrappers that force `choice_key` are **controls**, not product defaults.
- No human-brain / consciousness / AGI claims.

## Git

This workspace snapshot may lack `.git` → `git_commit.txt` may say `NO_GIT_REPOSITORY`.
