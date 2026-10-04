# Benchmark tick / GPU (auto)

- Generado por `experiments.bench_tick_gpu`
- GPU: `GPU solicitada (no disponible, usando CPU)`

| Perfil | LIF activas | ms/tick | RSS MB | Estado |
|--------|------------|---------|--------|--------|
| neuro-biológico | 624 | 16.36 | 56.9 | ok |
| neuro-10k | 10290 | 23.69 | 68.1 | ok |
| neuro-50k | 50010 | — | — | skip: 50k requires GPU (set CEREBRO_USE_GPU=1) or --force-heavy |

## HW mínimo (guía)

- **compact (~500 LIF):** CPU suficiente; CI / smoke.
- **10k (~10 290 LIF):** GPU NVIDIA + CuPy recomendada para batch paper.
- **50k (≥50 000 LIF):** GPU dedicada (p.ej. RTX 3050 4GB+); no correr en CI sin GPU.
- Nunca citar ensambles en disco como «neuronas activas».
