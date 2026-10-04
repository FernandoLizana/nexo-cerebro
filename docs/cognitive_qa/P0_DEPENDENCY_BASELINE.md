# P0 — Dependency baseline

**Checked:** 2026-08-18  
**Tool:** `python -m scripts.check_dependency_consistency` → `dependency consistency OK`  
**P0 action:** no version upgrades.

## Python expected

`pyproject.toml` → `requires-python = ">=3.11"`  
Measured: **Python 3.11.0** on **Windows-10-10.0.26200**.

## Direct dependencies (`pyproject.toml` / `requirements.txt`)

| Package | pyproject | requirements.txt | lock (`requirements-lock.txt`) |
|---------|-----------|------------------|--------------------------------|
| flask | `>=3.0,<4` | `>=3.0,<4` | `3.0.3` |
| numpy | `>=1.26,<3` | `>=1.26,<3` | `2.4.3` |
| scipy | `>=1.11,<2` | `>=1.11,<2` | `1.17.1` |
| pillow | `>=10.0,<13` | `>=10.0,<12` | `12.1.1` |
| pypdf | `>=4.0,<7` | `>=4.0,<7` | `6.10.2` |
| pyyaml | `>=6.0,<7` | `>=6.0,<7` | `6.0.3` |

## Optional

| Extra | Spec | Notes |
|-------|------|-------|
| `[dev]` | pytest `>=8.0,<9`, pytest-cov `>=5.0,<7` | CI uses `pip install -e ".[dev]"` |
| `[gpu]` / `requirements-gpu.txt` | `cupy-cuda12x>=13.0` | not required for v90 CPU baseline |
| OCR comments | pytesseract / easyocr | not declared as install extras |

## Inconsistencies (preexisting, not fixed in P0)

1. **Pillow upper bound:** `requirements.txt` says `<12`; `pyproject.toml` says `<13`; lock pins `12.1.1`. Consistency script uses the pyproject range (`<13`) so lock **passes**.
2. **Project version vs profile:** `nexo.__version__` / pyproject `0.2.0`; scientific profile is `integrated_v90`.
3. **`COMMIT_HASH.txt`** contains `NO_GIT_REPOSITORY` (stale snapshot from 2026-08-04). Real git HEAD at P0 freeze: `3a0233c3c4fe504bcad5b545d7bbc43d0e6c2608`. P0 did not overwrite `COMMIT_HASH.txt` (that file is an environment capture, not the source of truth when git exists).
4. **`ENVIRONMENT.json`** is likewise stale (`commit: NO_GIT_REPOSITORY`). Fresh capture: `artifacts/baseline/p0/environment.json`.

## Used but undeclared (observed; not installed by P0)

Scripts/docs mention GPU/OCR/web tools. Core v90 CPU path uses the declared scientific stack (numpy/scipy/yaml/flask). `psutil` is **not** a dependency; P0 performance baseline therefore omits RAM/CPU sampling.

## Unused-looking declared packages

Flask is required for `app.py` / unified demo, not for `IntegratedRuntime.run`. Pillow/pypdf serve curriculum/library, not the 12-tick golden run. They remain part of v90 and must stay declared.
