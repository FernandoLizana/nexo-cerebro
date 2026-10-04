# NEXO Sprint 16 — Replicación + permutación + CLI trace

## Alcance implementado

- **CLI `--trace-output`**: export automático de traza JSON desde `nexo.run`.
- **CLI `--replication-dir`**: paquete replicación (result + trace + config + manifest).
- **Auto-export YAML**: `tracing.export_path` y `replication.export_dir` en perfil.
- **`permutation_mode: integrated`**: p-values por permutación en `statistics_v2.json`.
- **`replication_mode: integrated`**: `replication_id` en `build_result()`.
- **Config**: `integrated_v16.yaml`

## Modos nuevos

```yaml
replication_mode: integrated
permutation_mode: integrated
```

## CLI

```powershell
python -m nexo.run --config configs/nexo/integrated_v16.yaml --trace-output results/traces/run.json
python -m nexo.run --config configs/nexo/integrated_v16.yaml --replication-dir results/replication/run1
```

## Paquete de replicación

```
results/replication/integrated_v16/
  result.json
  trace.json
  config.yaml
  manifest.json
```

## Verificación

```powershell
python -m pytest tests/test_replication_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v16.yaml
```

## Limitaciones honestas

- Permutación es test exploratorio, no corrección múltiple.
- Paquete de replicación no incluye event_log completo.
- p-value requiere ≥2 seeds por condición en batería.

## Perfil máximo acumulado

`integrated_v16`: v15 + replicación exportable + permutación + CLI trace.
