# P0 — Hardcoded actions audit

Search terms: eat, rest, flee, approach, explore, caregiver, inspect, move, food, drink, sleep, room.

False positives avoided:

- `nexo/sleep/` and `SleepArchitectureProcess` = sleep **module**, not REST action.
- `nexo/environment.py` = git/env snapshot.
- `brain/environment.py` = circadian clock.
- Drive key `"sleep"` in `DriveField` is a homeostatic drive, mapped into action `"rest"` via `action_bias`.

## DEMO-SPECIFIC

| Símbolo | Dónde | Notas |
|---------|-------|-------|
| `eat`, `rest`, `flee`, `explore`, `approach_caregiver`, `inspect_distractor` | `RoomWorld.available_actions` L40–49, `action_info` L51–70, `apply_action` L80–102 | catálogo canónico nexo |
| `seek_shelter` | `ExtendedRoomWorld` | PFC `ROOM_ACTION_SCHEMAS` **no** lo incluye |
| modalidades `food`, `caregiver`, `distractor`, `danger` | `percepts_for_agent` | sensores toy |
| `tv`, `research`, `study`, `wander`, `cook`, `harvest`, `hygiene`, `companion`, … | `nexo/demo/world2d_actions.py`; `brain/deliberation.py` `ACTION_SCHEMAS` | hogar + currículo |
| fridge/bed/desk/TV coords | `brain/world.py` `_build_home`, `_interact` | affordances GPS |
| `drink` | schemas brain; nexo mapea drink→**rest** | pérdida en adapter |
| `sleep` como `choice_key` | `ACTION_SCHEMAS`; mapeado a rest en nexo | distinto del módulo sueño |
| `move` | evento `type: "move"` en `World2D.apply_motor`; **no** hay acción nexo `move` | locomoción 0–3 |
| `inspect` | solo `inspect_distractor` | no hay inspect genérico |
| `water` | `hydration` corporal; no hay acción drink en RoomWorld | |

## DOMAIN-SPECIFIC (homeostasis/social, aún name-locked)

| Símbolo | Dónde | Clase |
|---------|-------|-------|
| hunger→eat, safety→flee, social→caregiver | `nexo/homeostasis/drives.py` `action_bias` | drives cableados a verbos demo |
| `MetabolismEngine.apply_action` eat/rest/caregiver | `nexo/body/metabolism.py` | fisiología nombrada como demo |
| allostasis goals `"eat"`/`"rest"` | `nexo/homeostasis/allostasis.py` | need = action id |
| ToM `approach_caregiver` | `nexo/social/theory_of_mind.py` | social + verbo demo |

## GENERIC COGNITIVE (mecanismo OK; tablas aún demo)

| Mecanismo | Archivo | Nota |
|-----------|---------|------|
| Selección competitiva + hábito | `nexo/basal_ganglia/gate.py` `ActionGate` | genérico; fallback `"rest"` no lo es |
| Predictive coding / tálamo | `nexo/core/process_perception.py` | genérico; bonuses food/eat no |
| TD `V(s,a)` | `nexo/reinforcement/td_learning.py` | genérico; `state_key` prefijo `room\|` es demo |
| WM / hipocampo | `nexo/core/process_memory.py` | genérico; always-encode eat/flee no |
| Cerebelo majority vote | `nexo/cerebellum/coordinator.py` | genérico sobre strings |
| Scheduler + event log | `nexo/core/scheduler.py`, `state_store.py` | genérico |
| Agency AST scan | `nexo/decision_audit.py` | genérico sobre `brain/` |

## P0 golden observation

v90 `world_mode: world_demo_facade`, seed 42, 12 ticks: **12× `explore`**. See `artifacts/baseline/p0/reproducibility/run_A.json`. That is real v90 behavior on this facade, not a test failure.
