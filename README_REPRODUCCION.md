# Reproducibilidad — NEXO Cerebro

## Requisitos

- Python **3.11+**
- Dependencias: ver `requirements.txt` o instalar editable:

```bash
python -m pip install -e ".[dev]"
```

GPU opcional: `pip install -e ".[gpu]"`

## Snapshot del entorno

Antes de experimentos, capture:

```bash
python -c "from nexo.environment import write_environment_files; write_environment_files()"
```

Genera `ENVIRONMENT.json` y `COMMIT_HASH.txt`.

**Nota:** el workspace actual puede no ser un repositorio git; en ese caso `commit=NO_GIT_REPOSITORY`.

## Verificación única

```bash
python -m scripts.verify_artifact
```

Salida: `reports/artifact_verification.json` y `reports/artifact_verification.md`.

Código de salida: `0`=pass, `1`=fail, `2`=partial.

## Tests

```bash
python -m pytest tests/ -q
```

Excluye automáticamente duplicados en `artifacts/` y `publication_finalization/` (ver `pyproject.toml`).

## Simulación determinista (baseline)

```python
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE
from nexo.experiment_conditions import get_condition

cond = get_condition("baseline")
brain = InfantApeBrain(
    profile=COMPACT_PROFILE,
    headless=True,
    auto_save=False,
    seed=42,
    condition_id=cond.condition_id,
    experiment_flags=cond.flags,
)
brain.world._rng = brain.random_streams.world
for _ in range(20):
    brain.world_tick(steps=1)
```

## Condiciones experimentales

| ID | Descripción |
|----|-------------|
| `baseline` | Paper histórico (roadmap OFF) |
| `roadmap100_full` | Todas las dinámicas roadmap ON |
| `roadmap100_safe` | Subconjunto CI |
| `no_binding` | Sin bind PFC↔límbico |
| `full` | **Alias legacy** = baseline (NO roadmap100) |

Definiciones: `configs/experiment_conditions.yaml` y `nexo/experiment_conditions.py`.

## Baterías

**CI (rápida):**

```bash
python -m pytest tests/test_reproducibility.py -q
python -m scripts.verify_artifact
```

**Paper (manual, costosa):**

```bash
python -m experiments.run_battery --config configs/battery_paper_full.yaml
```

## Empaquetado

```bash
python scripts/build_release_artifact.py
```

Genera `dist/NEXO_ROADMAP100_ARTIFACT_<version>.zip` sin rutas personales ni `.venv`.

## Semillas

- Semilla raíz: `InfantApeBrain(seed=...)`
- Flujos: `nexo.random_streams.RandomStreams` (world, neural, sensory, memory, decision, learning)
- **No** usar `default_rng(age_ticks)` para ruido de deliberación (corregido en `brain/deliberation.py`).

## Resultados

Cada ejecución debe incluir metadatos (`nexo.result_schema.ExperimentResult`):

- `config_hash`, `flags`, `seed`, `commit`, `trajectory_hash`

Esquema JSON: `schemas/experiment_result.schema.json`.
