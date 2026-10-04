# NEXO Sprint 15 — Trazabilidad integrada + WM→PFC

## Alcance implementado

- **WM→PFC (`routing_mode: integrated`)**: `EnhancedWorkingMemoryProcess` escala ítems WM por ganancia connectome.
- **Trazabilidad (`tracing_mode: integrated`)**: `IntegratedTraceCollector` + `IntegratedTraceProcess`.
- **Eventos**: `telemetry.trace` por tick con acción, energía y entregas connectome.
- **Export**: `runtime.export_trace(path)` → JSON con entries + summary.
- **Config**: `integrated_v15.yaml`

## Modo trazabilidad

```yaml
tracing_mode: integrated  # legacy | integrated
```

`build_result()` incluye `trace_events`, `trace_summary`.

## Export programático

```python
rt = IntegratedRuntime(cfg)
rt.run()
rt.export_trace(Path("results/traces/run.json"))
```

## Verificación

```powershell
python -m pytest tests/test_tracing_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v15.yaml
```

## Limitaciones honestas

- Traza compacta (no dump completo del event_log).
- WM→PFC modula payload WM, no buffer interno del deliberador.
- Export vía `export_trace()`, CLI `--trace-output`, o `tracing.export_path` en YAML.

## Perfil máximo acumulado

`integrated_v15`: v14 + trazabilidad + enrutamiento WM→PFC completo.
