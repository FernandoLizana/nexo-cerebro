# NEXO Sprint 17 — Tarea safety_escape + FDR + event_log

## Alcance implementado

- **Tarea `safety_escape`**: peligro elevado (0.85), métricas `flee_ratio`, `safety_response`.
- **Registro de tareas**: `nexo/behavioral/task_registry.py` para batería extensible.
- **`correction_mode: integrated`**: FDR Benjamini-Hochberg sobre `permutation_p` → `permutation_q`.
- **`eventlog_mode: integrated`**: export `event_log.json` en paquete de replicación.
- **Manifiesto v3**: 4 tareas incluyendo `safety_escape`.
- **Config**: `integrated_v17.yaml`

## Modos nuevos

```yaml
correction_mode: integrated
eventlog_mode: integrated
```

## Batería v3

```powershell
python -m experiments.integrated_battery.run_battery `
  --tasks survival safety_escape `
  --seeds 42 `
  --latency-mode integrated

python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v3.yaml
```

## Verificación

```powershell
python -m pytest tests/test_tasks_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v17.yaml
```

## Limitaciones honestas

- FDR controla falsos positivos de forma aproximada, no sustituye diseño experimental.
- `safety_escape` usa RoomWorld con 6 acciones, no entorno 3D.
- event_log exportado es compacto (max 2000 eventos recientes).

## Perfil máximo acumulado

`integrated_v17`: v16 + tarea escape + corrección FDR + event_log en replicación.
