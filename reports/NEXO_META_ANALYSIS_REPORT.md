# NEXO Sprint 18 — Meta-análisis entre réplicas + curiosity_explore

## Alcance implementado

- **`meta_analysis_mode: integrated`**: agrega paquetes de replicación bajo un directorio raíz.
- **`nexo/behavioral/meta_analysis.py`**: descubre `manifest.json`, resume consistencia (trajectory/metric consensus) y agrega métricas numéricas.
- **Resumen fenomenológico event_log**: `summarize_event_log_payload()` con conteos por tipo/fuente.
- **Tarea `curiosity_explore`**: bajo peligro (0.05), distractor saliente, métricas `explore_ratio`, `curiosity_score`.
- **Manifiesto v4**: 5 tareas incluyendo `curiosity_explore`.
- **Config**: `integrated_v18.yaml`

## Modos nuevos

```yaml
meta_analysis_mode: integrated
```

## Meta-análisis

```powershell
python -m nexo.run --config configs/nexo/integrated_v18.yaml

python -m nexo.run --config configs/nexo/integrated_v18.yaml `
  --meta-analysis-dir results/replication
```

Export: `results/meta_analysis/integrated_v18_summary.json`

## Batería v4

```powershell
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v4.yaml
```

## Verificación

```powershell
python -m pytest tests/test_meta_analysis_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v18.yaml
```

## Limitaciones honestas

- Meta-análisis escanea solo subdirectorios inmediatos con `manifest.json`.
- Consenso de trayectoria no implica equivalencia fenomenológica completa.
- `curiosity_explore` usa RoomWorld simplificado, no entorno abierto 3D.
- Resumen event_log es agregado, no narrativa fenomenológica.

## Perfil máximo acumulado

`integrated_v18`: v17 + meta-análisis entre réplicas + tarea curiosidad + resumen event_log.
