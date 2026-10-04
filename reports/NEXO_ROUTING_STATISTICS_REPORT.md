# NEXO Sprint 14 — Enrutamiento ampliado + estadística de batería

## Alcance implementado

- **Enrutamiento (`routing_mode: integrated`)**: hippocampus→PFC escala recuperación episódica; global_workspace→PFC escala bias del workspace.
- **Auditoría**: `ConnectomeRoutingAuditProcess` emite `connectome.routing_active` para 3 aristas extendidas.
- **Estadística (`statistics_mode: integrated`)**: bootstrap CI, Cohen's d vs baseline, agregación multi-seed.
- **Manifiesto v2**: exporta `statistics_v2.json` cuando `statistics_mode: integrated`.
- **Config**: `integrated_v14.yaml`

## Modos nuevos

```yaml
routing_mode: integrated      # legacy | integrated
statistics_mode: integrated  # legacy | integrated (export manifiesto)
```

## Estadística exportada

- Media, desvío estándar, IC bootstrap por métrica
- Cohen's d vs `integrated_full` + `lesion_none`
- Agregación por tarea × ablación × lesión

## Verificación

```powershell
python -m pytest tests/test_routing_statistics_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v14.yaml
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v2.yaml
```

## Limitaciones honestas

- Bootstrap descriptivo, no prueba de hipótesis formal.
- Enrutamiento extendido en memoria episódica, workspace y memoria de trabajo (WM→PFC).
- Cohen's d asume comparabilidad entre seeds.

## Perfil máximo acumulado

`integrated_v14`: v13 + enrutamiento ampliado + estadística de batería.
