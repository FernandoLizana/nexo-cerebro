# NEXO Sprints 43–46 — Fase 7 (peso, figuras, pipeline paper, v46)

## Sprint 43 — Peso deliberación configurable
- **`deliberation_weight_mode: integrated`** + **`legacy_advisory_weight`** (0–1)
- `DeliberationWeightProcess` → `action.weighted` (sustituye unified cuando activo)
- **Tarea `deliberation_weight_sweep`**

## Sprint 44 — Figuras paper SVG
- **`paper_figures_mode: integrated`**
- `battery_scores.svg` + snippet LaTeX (sin matplotlib)

## Sprint 45 — Pipeline paper E2E
- **`pipeline_paper_mode: integrated`**
- `run_pipeline_paper()`: batería → CSV/LaTeX → figuras SVG
- Fix `battery_paper` para reportes JSON en formato lista

## Sprint 46 — Publicación completa v46
- Bundle full incluye `figures/`
- **Manifiesto v11** (13 tareas) | **Perfil máximo**: `integrated_v46.yaml`

## Verificación

```powershell
python -m pytest tests/test_sprints_43_46_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v46.yaml --ticks 18
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v11_mini.yaml
```

## Roadmap integrado

**Sprints 1–46 completos.**
