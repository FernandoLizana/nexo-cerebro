# NEXO Sprints 19–22 — Batch, cross-batería, fenomenología y social

## Sprint 19 — Réplicas multi-seed

- **`replication_batch_mode: integrated`**
- **`nexo/behavioral/replication_batch.py`**: exporta `seed_{N}/` + `batch_summary.json`
- CLI: `--replication-batch-seeds 42 99 --replication-batch-dir results/replication/batch`

## Sprint 20 — Cross-batería

- **`cross_battery_mode: integrated`**
- **`nexo/behavioral/cross_battery.py`**: compara medias primarias entre informes JSON (v3 vs v4)
- Config `cross_battery.reports` + `export_path`

## Sprint 21 — Fenomenología compacta

- **`phenomenology_mode: integrated`**
- **`nexo/behavioral/phenomenology.py`**: ventanas temporales con highlights (acción, lenguaje, meta)
- Export `phenomenology.json` en paquete de replicación

## Sprint 22 — Tarea social + perfil máximo

- **Tarea `social_approach`**: cuidador presente, métricas `approach_ratio`, `social_score`
- **Manifiesto v5**: 6 tareas, ablación `abl_no_social`
- **Perfil máximo**: `integrated_v22.yaml`

## Modos nuevos (19–21)

```yaml
replication_batch_mode: integrated
cross_battery_mode: integrated
phenomenology_mode: integrated
```

## Verificación

```powershell
python -m pytest tests/test_sprints_19_22_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v22.yaml --ticks 35
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v5.yaml
```

## Limitaciones honestas

- Batch multi-seed no corre automáticamente en demo (requiere CLI o `replication.auto_batch: true`).
- Cross-batería requiere informes JSON previos en disco.
- Fenomenología es agregado por ventanas, no narrativa subjetiva.
- `social_approach` usa RoomWorld simplificado.

## Roadmap integrado

**Sprints 1–22 completos.** Perfil acumulado: `integrated_v22`.
