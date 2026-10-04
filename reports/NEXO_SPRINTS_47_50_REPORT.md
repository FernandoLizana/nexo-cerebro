# NEXO Sprints 47–50 — Fase 8 (LaTeX, batería full, pipeline auto, release)

## Sprint 47 — LaTeX maestro
- **`latex_master_mode: integrated`**
- `nexo_integrated_master.tex` une métricas + batería + figuras
- Export: `latex_master_export`

## Sprint 48 — Batería completa + FDR
- **`battery_full_mode: integrated`**
- `run_battery_full()` → `battery_full_summary.json` con estadística/FDR

## Sprint 49 — Pipeline paper auto
- **`pipeline_paper.auto_run: true`**
- `run_pipeline_paper_auto()`: batería → tablas → SVG → LaTeX maestro

## Sprint 50 — Release bundle
- **`release_bundle_mode: integrated`**
- `release_manifest.json` + `REPRODUCE.txt` + checksums SHA256
- **Perfil máximo**: `integrated_v50.yaml` · batería v12

## Verificación

```powershell
python -m pytest tests/test_sprints_47_50_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v50.yaml --ticks 12
```

## Roadmap integrado

**Sprints 1–50 completos.**

## Nota git

Inicializar repo y tag `integrated_v50` queda a criterio del usuario (`git init` + commit manual).
