# NEXO Sprint 13 — Análisis comparativo + manifiesto reproducible

## Alcance implementado

- **Huellas (`nexo/behavioral/fingerprint.py`)**: vector compacto + hash de métricas.
- **Comparación (`nexo/behavioral/comparison.py`)**: deltas vs `integrated_full` + `lesion_none`, ranking L1.
- **Manifiesto (`nexo/behavioral/manifest.py`)**: batería reproducible desde YAML con export JSON/benchmark/comparison.
- **Runtime**: `analysis_mode: integrated` activa `BehavioralFingerprintProcess` (periodo 30).
- **Runner**: `experiments/integrated_battery/run_manifest.py`
- **Config**: `integrated_v13.yaml`, `battery/integrated_v2.yaml` (export comparison)

## Modo análisis

```yaml
analysis_mode: integrated  # legacy | integrated
```

Emite `behavior.fingerprint` y `metric_fingerprint` en `build_result()`.

## Manifiesto reproducible

```powershell
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v2.yaml
```

Genera:
- `report_v2.json` — corridas crudas
- `benchmark_v2.json` + `.csv` — agregados
- `comparison_v2.json` — deltas vs baseline + ranking

## Verificación

```powershell
python -m pytest tests/test_analysis_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v13.yaml
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v2.yaml
```

## Limitaciones honestas

- Comparación usa distancia L1 simple, no inferencia estadística.
- Baseline fijo: `integrated_full` + `lesion_none`.
- Huella conductual es proxy observable, no diagnóstico.

## Perfil máximo acumulado

`integrated_v13`: v12 + análisis comparativo + huellas conductuales.
