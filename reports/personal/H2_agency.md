# H2 — Agency auditable bajo motor integrado

**Fecha:** 2026-08-08  
**Perfil:** `integrated_v90`  
**Hipótesis:** El certificado causal puede validar agency tick-a-tick cuando la selección de acción ocurre antes del certificado.

## Fix técnico (Sprint 75)

| Antes | Después |
|-------|---------|
| `CausalCertificateProcess` priority 65 (pre-selección) | priority **50** (post-motor 55) |
| `UnifiedMotorProcess` priority 63 (pre-BG) | priority **58** (post-BG 60) |
| Solo `action.selected` | Fallback a `unified.motor.integrated_action` + `reward_value` |

Campos nuevos: `action_source`, `agency_valid`, `reward_linked_rate`.

## Script

```powershell
python -m experiments.personal.run_h2_agency_audit --seed 42 --ticks 80
```

Artefacto: `results/personal/H2_agency/h2_agency_audit_seed42.json`

## Resultados (80 ticks interactivos, seed 42)

| Métrica | Valor |
|---------|-------|
| `agency_valid_rate` | **1.0** |
| `certificate_valid_rate` | **1.0** |
| `motor_agreement_rate` | **1.0** |
| `valid_certificates` | 80/80 |

## Integración Fase 15

- `agency_audit_mode` exporta `results/agency_audit/integrated_v90_audit.json`
- `science_bundle_mode` enlaza bitácoras H1+H2 y scripts reproduce

## Conclusión

Agency deja de ser decorativa: el certificado se emite **después** de la cadena selección→motor→recompensa y distingue fuente de acción.
