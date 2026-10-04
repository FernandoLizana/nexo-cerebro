# Perfiles neuronales y experimentos — convención única

Este documento es la **fuente de verdad** para evitar mezclar escalas al citar Nexo.

## Tabla de perfiles

| Perfil | CLI / env | ~Neuronas LIF activas | Sensory | Motor | Uso | ¿Resultados paper E1–E3? |
|--------|-----------|------------------------|---------|-------|-----|--------------------------|
| `COMPACT_PROFILE` | `--profile compact` | ~500 | 128 | 28 | CI, smoke tests, repro en minutos | **No** |
| `INFANT_APE_PROFILE` | (interno) | ~340 | 96 | 24 | Curriculum bebé-simio | **No** |
| `VIRTUAL_LARGE_PROFILE` | `--profile large` | ~1.400 | 384 | 72 | Demo Flask interactiva (`app.py`, default) | **No** |
| **`SCALE_10K_PROFILE`** | `--profile 10k` | **~10.290** | 2560 | 320 | Batch GPU, ablaciones publicadas | **Sí** |
| `SCALE_50K_PROFILE` | `--profile 50k` | **≥50.000** LIF | 12800 | 1600 | Fase 3 / GPU (RTX 3050+); ensambles virtuales siguen en disco | **No** (aún) |

Cálculo: `profile_neuron_count()` en `brain/profile.py` (corteza E/I + hipocampo + 4× lóbulos).

**Citar siempre:** *active LIF* ≠ *disk-indexed virtual*. El perfil 50k no implica 50k ensambles en disco.
## Capas de escala (Connectome Scaffold)

| Capa | Escala | Módulo |
|------|--------|--------|
| Núcleo activo LIF | ~500–≥50k | `cortex`, `hippo`, episodios (`SCALE_50K_PROFILE`) |
| Ensambles virtuales | ~90M (disco) | `virtual_assembly.py` → también columnas `lobe_cortex` si `enable_lobe_virtual_inject` |
| Connectome lógico | ~86B neuronas, ~10¹⁴ sinapsis est. | `connectome_blueprint.py`, `cortical_chunks.py` |

Seed fija (`connectome_seed=42`): mapa procedural reproducible. Flag `enable_connectome_scaffold` en `AblationFlags` (default **off** en batch paper; condición `scaffold` para E6).

## Regla de citación

1. **Tablas, CSV y figuras del paper** → siempre **`SCALE_10K_PROFILE`** (`experiments/results/`, `experiments/figures/`).
2. **“Mesoescala”** describe la *familia* de perfiles (~500–~10.290), no un único tamaño.
3. **No escribir** “los experimentos usan COMPACT” ni “~500–1.4k neuronas” como escala experimental del paper.
4. **Demo Flask** (~1.4k) comparte código pero **no** es el harness E1–E3.

## Comandos

```bash
# Reproduce resultados del paper (E1 + E2 + E3 + figuras)
python -m experiments.run_all --profile 10k --seeds 5 --steps 200 --workers 2

# Smoke test rápido (~500 neuronas) — NO sustituye al paper
python -m experiments.run_all --profile compact --seeds 1 --steps 50

# Escala 50k LIF (GPU recomendada; no es el harness paper E1–E3)
python -c "from brain.profile import SCALE_50K_PROFILE, profile_neuron_count; print(profile_neuron_count(SCALE_50K_PROFILE))"

# Benchmark tick / memoria (50k se omite sin GPU salvo --force-heavy)
python -m experiments.bench_tick_gpu --profiles compact,10k --ticks 5
python -m experiments.bench_tick_gpu --profiles compact,10k,50k --ticks 3
```

## HW mínimo (guía)

| Perfil | LIF activas | Requisito práctico |
|--------|-------------|-------------------|
| compact | ~500 | CPU; CI |
| 10k | ~10 290 | GPU NVIDIA + CuPy recomendada |
| 50k | ≥50 000 | GPU dedicada (p.ej. RTX 3050 4GB+); no CI sin GPU |

## Variables de entorno relevantes

| Variable | Valor paper | Notas |
|----------|-------------|-------|
| `CEREBRO_EXPERIMENT_PROFILE` | `10k` | Default en `run_all.py` / batch |
| `CEREBRO_USE_GPU` | `1` (E1/E3) | E2 fuerza CPU por determinismo |
| `CEREBRO_OLLAMA` | `0` (E1/E3) | E2 compara 0 vs 1 |

## Documentos alineados con esta convención

- `docs/paper/paper_completo.md` — paper largo
- `docs/paper/draft_workshop.md` — borrador workshop
- `docs/paper/architecture.md` — arquitectura formal
- `docs/paper/resumen_implementacion_completo.md` — resumen de implementación
- `experiments/README.md` — reproducibilidad
