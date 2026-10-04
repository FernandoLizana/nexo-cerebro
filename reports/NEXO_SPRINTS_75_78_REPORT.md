# NEXO Sprints 75–78 — Fase 15

**Perfil:** `integrated_v90`  
**Batería:** v19 (33 tareas) / v19_mini (4 tareas CI)

## Sprints

| Sprint | Entrega | Flag |
|--------|---------|------|
| 75 | Certificado causal v2 — post-motor + `agency_valid` | fix priorities + `causal_certificate_mode` |
| 76 | `agency_audit_mode` — auditoría agency integrada | `agency_audit_mode: integrated` |
| 77 | `science_bundle_mode` — envelope reproducible H1+H2 | `science_bundle_mode: integrated` |
| 78 | Perfil v90 + batería v19 + bitácora H2 | tag `integrated_v90` |

## Verificación

```powershell
python -m pytest tests/test_sprints_75_78_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v90.yaml --ticks 12
python -m experiments.personal.run_h2_agency_audit
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v19_mini.yaml
```

## Limitaciones

- `agency_score` depende de ticks con acción seleccionada (sueño = certificado inválido)
- `science_bundle` referencia artefactos personales si existen en `results/personal/`
- Lesión connectome en H1.3 ≠ `agency_audit`; son capas distintas
