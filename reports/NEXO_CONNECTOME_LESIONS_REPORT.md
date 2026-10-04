# NEXO Sprint 11 — Lesiones connectome fine-grained

## Alcance implementado

- **Lesiones (`nexo/interventions/`)**: `LesionState`, `LesionSpec`, perfiles declarativos.
- **Router**: aristas severadas → señal cero; escalado parcial vía `weight_scale`.
- **Runtime**: `intervention_mode: integrated` aplica `lesion_profile` al iniciar.
- **Auditoría**: `ConnectomeLesionAuditProcess` emite `connectome.lesion_applied` en tick 0.
- **Enrutamiento ejecutivo**: BG escala boost episódico (hippo→PFC) y deliberación (PFC→BG).
- **Config**: `configs/nexo/integrated_v11.yaml`, `configs/interventions/lesion_profiles_v1.yaml`

## Modo intervención

```yaml
intervention_mode: integrated  # legacy | integrated
lesion_profile: lesion_none    # ver registro abajo
```

## Perfiles de lesión

| ID | Efecto |
|----|--------|
| `lesion_none` | Conectoma intacto |
| `lesion_sever_hippo_pfc` | Corte hippocampus → prefrontal |
| `lesion_sever_pfc_bg` | Corte prefrontal → basal_ganglia |
| `lesion_sever_thal_visual` | Corte thalamus → visual_cortex |
| `lesion_weaken_pfc_bg` | Peso PFC→BG al 25% |
| `lesion_delay_pfc_bg` | +5 ticks latencia PFC→BG (metadato) |

## Verificación

```powershell
python -m pytest tests/test_intervention_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v11.yaml
```

## Limitaciones honestas

- Latencia de aristas bufferizada en runtime (`latency_mode: integrated`).
- Lesiones sobre aristas no enrutadas en procesos no alteran conducta.
- Perfiles acotados a `connectome_v1.yaml` (15 módulos).

## Perfil máximo acumulado

`integrated_v11`: v10 + intervenciones connectome.
