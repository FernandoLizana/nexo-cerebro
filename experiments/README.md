# Experimentos reproducibles (paper Nexo)

Runner **headless** (sin Flask/UI) para ablaciones E1–E3 y figuras del workshop.

## Perfiles: cuál usar

| Perfil | CLI | ~Neuronas | Para qué |
|--------|-----|-----------|----------|
| **`SCALE_10K_PROFILE`** | `--profile 10k` | ~10.290 | **Resultados del paper** (CSV/figuras en `results/`) |
| `COMPACT_PROFILE` | `--profile compact` | ~500 | Smoke test / CI (~minutos) |
| `VIRTUAL_LARGE_PROFILE` | `--profile large` | ~1.400 | Mismo código que demo Flask; no usado en E1–E3 |

**No mezclar:** los números de `experiments/results/` son **solo 10k**. Compact es validación rápida, no sustituto del paper. Convención completa: [`docs/paper/perfiles_y_experimentos.md`](../docs/paper/perfiles_y_experimentos.md).

## Requisitos

```bash
pip install -r requirements.txt
```

Variables útiles:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `CEREBRO_EXPERIMENT_PROFILE` | `10k` (default en batch paper) | `compact` (~500) o `10k` (~10.290 neuronas) |
| `CEREBRO_USE_GPU` | `1` en batch | CuPy/CUDA — RTX acelera spmv sináptico |
| `CEREBRO_GPU_MAX_STEPS` | `999999` | Pasos GPU por episodio (modo agresivo) |
| Perfil | `SCALE_10K_PROFILE` | ~10k neuronas; 2 workers en RTX 6GB |

## Comando único (10k — reproduce resultados del paper)

```bash
python -m experiments.run_all --profile 10k --seeds 5 --steps 200 --workers 2
```

## Paralelo manual

```bash
# Varios seeds a la vez (2 procesos → 2 simulaciones en GPU)
python -m experiments.run_parallel --profile 10k --condition full --seeds 5 --workers 2

# E1 completo: 5 condiciones × seeds, 2 workers
python -m experiments.run_e1_parallel --profile 10k --seeds 5 --workers 2 --parallel-seeds 2
```

Genera:

- `experiments/results/e1_*_summary.csv` — agregados por condición
- `experiments/results/e1_*_s*.jsonl` — métricas por tick
- `experiments/results/e2_llm_invariance.csv`
- `experiments/results/e3_sleep_recall.csv`
- `experiments/results/e4_sleep_selective.csv` — E4 sueño selectivo
- `experiments/results/e5_grounding.csv` — E5 grounding
- `experiments/results/e7_multimodal.csv` — E7 ablación multimodal
- `experiments/results/bench_tick_gpu.csv` — latencia/tick
- `experiments/figures/fig1–fig8.png`

## Comandos individuales

```bash
# E1 — una condición
python -m experiments.run_batch --condition nobind --seeds 10 --steps 300

# E2 — LLM off vs on
python -m experiments.run_batch --e2 --seeds 5 --steps 100

# E3 — sueño vs control
python -m experiments.run_sleep --seeds 5

# E4 — sueño selectivo (usar CEREBRO_SKIP_PROCESS_GUARD=1 si hay otros runners)
python -m experiments.run_e4_sleep_selective --seeds 5 --profile compact

# E5 — grounding
python -m experiments.run_e5_grounding --seeds 5 --profile compact

# E7 — multimodal
python -m experiments.run_e7_multimodal --seeds 5 --profile compact

# Arena Level 2 — sed + fuente desconocida (1ª vs 2ª exposición)
python -m experiments.run_arena_thirst --seeds 3 --profile compact

# Bench tick/GPU
python -m experiments.bench_tick_gpu --profiles compact,10k --ticks 5

# Solo figuras (tras correr experimentos)
python -m experiments.plot_figures --in experiments/results
```

## Condiciones de ablación

| CLI | Flag (`brain/experiment_flags.py`) |
|-----|-------------------------------------|
| `full` | baseline |
| `nobind` | `bind_deliberation=False` |
| `nopfc` | `force_limbic_winner=True` |
| `nohippo` | `disable_hippocampus=True` |
| `noaffect` | `disable_affect=True` |

## Métricas por tick

- `deliberation.agency`, `inhibited`
- `intention_circuit.spike_aligned`, `pfc_veto`
- `remembered`, `cognition.prediction.surprise`
- `drive_coherent` — acción vs drive dominante

Ver `experiments/metrics.py`.

## Documentación del paper

- Arquitectura formal: `docs/paper/architecture.md`
- Borrador workshop: `docs/paper/draft_workshop.md`
