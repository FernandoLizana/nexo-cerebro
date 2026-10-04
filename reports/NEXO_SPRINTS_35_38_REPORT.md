# NEXO Sprints 35–38 — Fase 5 (fusión, World2D full, GPU CI, paper pack)

## Sprint 35 — Fusión deliberación
- **`deliberation_fusion_mode: integrated`**
- `DeliberationFusionProcess` + eventos `deliberation.fusion`
- Política honesta: **`integrated_wins`** (legacy sigue advisory)
- Export: `deliberation_fusion_export`

## Sprint 36 — Catálogo completo World2D
- **`world2d_full_actions_mode: integrated`**
- `FULL_LEGACY_CATALOG` alineado con `CHOICE_EVENT_MAP`
- Acción `flee` en World2D lite
- **Tarea `world2d_full_navigation`**

## Sprint 37 — Bench GPU CI-safe
- **`gpu_bench_mode: integrated`**
- `nexo/behavioral/gpu_bench.py`: respeta `NEXO_SKIP_GPU_BENCH`
- Bench mínimo (`ticks: 1`, `skip_heavy`) — no LIF en scheduler integrado

## Sprint 38 — Paper pack CSV + LaTeX
- **`paper_pack_mode: integrated`**
- `metrics.csv`, `metrics_table.tex`, manifest
- **Manifiesto v9** (10 tareas) | **Perfil máximo**: `integrated_v38.yaml`

## Verificación

```powershell
python -m pytest tests/test_sprints_35_38_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v38.yaml --ticks 18
```

## Roadmap integrado

**Sprints 1–38 completos.**
