# Nexo Level 2 — aprendizaje causal

Estado: **V2.5** (discriminación + demo HUD + nota paper).

## Objetivo

`objeto + interacción + necesidad dominante → cambio corporal observado`

Evidencia acotada para PFC; **nunca** escribe `choice_key` fuera de deliberación.

## V2.5 — discriminación, demo, paper

### Discriminación bueno/malo

- `world.dry_object_ids` — sequedad por instancia (no solo flag global).
- Navegación: prior al `object_id` exitoso presente; tipo solo si desapareció (transfer).
- Arena: `task_discrimination.py` + `python -m experiments.run_arena_level25`.

### Demo HUD

- Panel «Decisión causal» + `GET /api/neural/causal/hud`.
- Smoke CI: `pytest tests/test_demo_hud.py` (Flask test client; no deja servidor).

```bash
set CEREBRO_DEMO_LITE=1
set CEREBRO_AFFORDANCES=1
set CEREBRO_COUNTERFACTUAL=1
set CEREBRO_TELEMETRY=1
python app.py
```

### Paper

- `docs/paper/level2_causal_learning.md` — claim + agency + runners.
- `docs/paper/draft_workshop.md` — §3.4 + E4 Arena.
- `docs/paper/architecture.md` — capa causal en diagrama.

E1–E3 a 10k **no** se reemplazan; Arena compact es evidencia adicional.

## Resumen de versiones

| Ver | Contenido |
|-----|-----------|
| 2.1 | AffordanceMap + drink/eat |
| 2.2 | Arena thirst + telemetría |
| 2.3 | HUD, contrafactual, hambre, sueño, demo-lite |
| 2.4 | Transferencia, schemas causales, higiene, física |
| 2.5 | Discriminación, demo HUD CI, nota paper |

## Tests

```bash
python -m pytest tests/test_level23.py tests/test_level24.py tests/test_level25.py tests/test_demo_hud.py -q
```

## Pendiente real restante

- Autores / affiliation / email / license → rellenar `docs/paper/AUTHORS.template.md`.
- PDF CLEI maquetado (tras autores).
- E8 Arena a 10k multi-seed (smoke 1 seed ya en `experiments/results/arena_10k/`).

Resultados compact en `experiments/results/arena_*.json`; figura `experiments/figures/fig9_e8_causal_arena.png`.
