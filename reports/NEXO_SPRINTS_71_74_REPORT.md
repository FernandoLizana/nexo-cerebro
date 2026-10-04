# NEXO Sprints 71–74 — Fase 14

**Perfil:** `integrated_v80`  
**Batería:** v18 (31 tareas) / v18_mini (4 tareas CI)  
**Flask demo:** `flask_unified_v4.yaml`

## Sprints

| Sprint | Entrega | Flag |
|--------|---------|------|
| 71 | `memory_unification_mode` — promoción hippo→SQLite tras consolidación | `memory_unification_mode: integrated` |
| 72 | `causal_certificate_mode` — certificado causal por tick | `causal_certificate_mode: integrated` |
| 73 | `day_in_the_life_mode` — simulación 24h acelerada + timeline JSON | `day_in_the_life_mode: integrated` |
| 74 | Perfil v80 + batería v18 + bitácora personal H1 | tag `integrated_v80` |

## Verificación

```powershell
python -m pytest tests/test_sprints_71_74_integrated.py -q
python -m nexo.run --config configs/nexo/integrated_v80.yaml --ticks 12
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v18_mini.yaml
python -m experiments.integrated_battery.run_manifest --manifest configs/battery/integrated_v18.yaml
python -m experiments.personal.run_h1_memory_day
```

## Verificación ejecutada (2026-08-07)

| Corrida | Resultado |
|---------|-----------|
| `test_sprints_71_74_integrated.py` | 10 passed |
| `integrated_v18_mini` | 4 tareas OK |
| `integrated_v18` full | **496 runs**, 156 agregados, 361 efectos, FDR OK |
| H1 24h (seed 42) | 288 ticks, 5 ciclos sueño, **0 promociones** (0 episodios hippo) |

## Limitaciones (honestas)

- `memory_unification` promueve solo episodios ya consolidados; requiere `legacy_brain` con `memory_store`
- `causal_certificate` documenta evidencia; no reemplaza trazabilidad completa del agent loop legacy
- `day_in_the_life` es acelerado (288 ticks × 300s); no simula latencia real de UI Flask
- Promoción usa umbral de confianza mínima (`PROMOTION_MIN_CONFIDENCE = 0.35`)
