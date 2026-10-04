# NEXO Sprint 12 — Latencia connectome + batería con lesiones

## Alcance implementado

- **Buffer temporal (`nexo/connectome/latency_buffer.py`)**: cola de entrega por tick.
- **Router**: `latency_mode: integrated` activa diferimiento; `legacy` enruta al instante.
- **Scheduler**: `advance_tick()` entrega señales antes de cada ciclo de procesos.
- **Auditoría**: `ConnectomeDeliveryProcess` emite `connectome.signal_delivered`.
- **Batería**: `--lesions`, `--latency-mode`, `--benchmark` en `run_battery.py`.
- **Benchmark**: `nexo/behavioral/benchmark.py` exporta JSON + CSV agregado.
- **Config**: `integrated_v12.yaml`, `battery/integrated_v2.yaml`

## Modo latencia

```yaml
latency_mode: integrated  # legacy | integrated
```

Con `integrated`, aristas con `latency_ticks > 0` (o `latency_add` por lesión) encolan señal y entregan en tick futuro.

## Batería ampliada

```powershell
python -m experiments.integrated_battery.run_battery `
  --seeds 42 `
  --ablations integrated_full `
  --lesions lesion_none lesion_delay_pfc_bg `
  --latency-mode integrated `
  --benchmark results/integrated_battery/benchmark_v2.json
```

## Verificación

```powershell
python -m pytest tests/test_latency_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v12.yaml
```

## Limitaciones honestas

- Buffer por arista enrutada vía `router.route()`; no simula colas biológicas completas.
- Señales entregadas persisten en buffer hasta sobrescritura (última entrega gana).
- Latencia no afecta procesos que no usan el router.

## Perfil máximo acumulado

`integrated_v12`: v11 + latencia bufferizada + batería con lesiones.
