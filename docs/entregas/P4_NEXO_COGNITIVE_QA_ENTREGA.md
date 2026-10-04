# P4 — NEXO Cognitive QA · entrega

**Fecha:** 2026-08-19 · **Fase:** P4 · **Veredicto:** PASS  
**Tema:** Goal Semantics, Task Context, Autonomous Objective Reasoning

---

## 1. Resumen ejecutivo

P4 cierra `P2_LIMITATION_GOAL_SEMANTICS`: NEXO puede recibir un **objetivo declarativo en lenguaje natural limitado** y usarlo como **intención activa** para modular deliberación y evaluar progreso — **sin** recibir la secuencia correcta de pasos del harness de test.

Flujo conceptual logrado:

```text
GOAL → INTENTION → PERCEPTION → GOAL RELEVANCE → DELIBERATION → ACTION → OUTCOME → PROGRESS → NEXT DECISION
```

**Evidencia:** 22 tests P4 PASS · P3/P2/P1 regression PASS · v90 golden intacto.

---

## 2. Estado recibido desde P3

| Entregable P3 | Estado en P4 |
|---------------|--------------|
| `PerceptualScene` / HYBRID | Preservado |
| `PerceptualAttentionGate` | Preservado |
| Action requires perception | Preservado |
| Selector secrecy | Preservado |
| `BrowserWorld.goal: str` | Ahora consumido vía `bind_task` |

Limitación heredada resuelta en P4: el string `goal` en `BrowserWorld` no llegaba al PFC.

---

## 3. Arquitectura antes / después

### Antes

```text
IntegratedRuntime → BrowserWorld → PerceptualScene → actions
                  (homeostatic goals: survive, eat, …)
                  browser_lab.GOAL = metadata ignorado por PFC
```

### Después

```text
parse_goal(GOAL) + TaskContext
       ↓
bind_task(rt, goal, task_context, world)
       ↓
TaskGoalProcess → goals.updated | goal.relevance | goal.progress
       ↓
PrefrontalDeliberator (+ goal_relevance) → EnhancedBasalGangliaProcess
       ↓
BrowserWorld (P3) → outcome → evaluate_progress()
```

---

## 4. Goal model

Ver `docs/cognitive_qa/P4_GOAL_MODEL.md`.

- Campos: `goal_id`, `description`, `goal_type`, `status`, `constraints`, `entities`, `subgoals`
- **Sin:** steps, selectors, expected_action_sequence
- Estados: PENDING → ACTIVE → PARTIALLY_SATISFIED | SATISFIED | BLOCKED | …
- Inmutabilidad semántica: web content no reescribe TASK_GOAL

---

## 5. TaskContext

Ver `docs/cognitive_qa/P4_TASK_CONTEXT.md`.

```yaml
user_name: "Nexo Test"
email: "nexo@example.test"
desired_plan: "Pro"
```

Solo datos agente-visibles. Oracle y selectores **prohibidos**.

---

## 6. Parser (NL limitado)

Ver `docs/cognitive_qa/P4_GOAL_PARSER.md`.

- Sin LLM obligatorio
- ES/EN básico, synonym map genérico
- Salida: dominio, entidades, constraints, subobjetivos semánticos
- Prohibido codificar pasos del Web Lab

---

## 7. Entities y constraints

| Entity | Source |
|--------|--------|
| `plan` | NL + TaskContext.desired_plan |
| `name`, `email` | TaskContext |

| Constraint | Effect |
|------------|--------|
| `must_select_plan` | Progress + relevance |
| `must_use_email` | Context binding |
| `must_not_leave_allowed_origin` | Policy (P2) |

---

## 8. Goal relevance

Ver `docs/cognitive_qa/P4_GOAL_RELEVANCE.md`.

- Heurística token/entity overlap
- Integrado en PFC (`+0.35`) y BG (`+0.18`) y net deliberation (`+0.22`)
- **No** anula visibilidad offscreen (P3)

---

## 9. Atención

P4 no duplica `PerceptualAttentionGate`. Goal relevance es señal **adicional** en deliberación. Separación documentada:

- visibility ≠ attention ≠ goal_relevance

---

## 10. Progress model

Ver `docs/cognitive_qa/P4_PROGRESS_MODEL.md`.

- Ordinal: none → partial → high → complete
- Basado en URL, historial observado, constraints
- **Anti-cheat:** no step count

---

## 11. Subgoals y recovery

Ver `docs/cognitive_qa/P4_SUBGOALS_AND_RECOVERY.md`.

- Subobjetivos semánticos del parser (no tabla REGISTER_PRO)
- Wrong choice → nuevo URL sin auto-corrección
- `goal.behavior_loop`, `goal.drift` — audit only

---

## 12. Loop / stagnation

`LoopDetector`: repeticiones A→B→A→B y estancamiento URL. Eventos internos, sin KPI comercial.

---

## 13. Oracle separation

Ver `docs/cognitive_qa/P4_ORACLE_SEPARATION.md`.

- `nexo_qa/scenarios/oracle.py` — **solo tests**
- `success_predicate(url, required_plan=...)` nunca en deliberación

---

## 14. Instruction authority

Ver `docs/cognitive_qa/P4_INSTRUCTION_AUTHORITY.md`.

```text
1. SYSTEM POLICY
2. TASK GOAL
3. TASK CONTEXT
4. ENVIRONMENT OUTCOME
5. WEB CONTENT
```

Fixture: `adversarial.html`

---

## 15. Web Lab P4

Ver `docs/cognitive_qa/P4_WEB_LAB.md`.

- Flujo P2 intacto + `adversarial.html`
- `task_definition.py` — register_pro, find_pricing, select_pro

---

## 16. Tareas autónomas

Tests:

- `test_register_pro_autonomous_attempt` — 96 ticks, seed 42
- `test_find_pricing_autonomous`

Mecanismo demostrado; éxito Pro **no garantizado** en todos los seeds.

---

## 17. Causal trace

Eventos emitidos:

```text
goals.updated (source=TASK_GOAL)
goal.progress
goal.relevance
action.selected
reward.received
```

Test: `test_goal_causal_trace_events`

---

## 18. Agency

- Goal dado · path **no** dado · acciones dinámicas · decisión NEXO
- Test: `test_agency_goal_given_path_not_given`

---

## 19. Tests

| Suite | Result |
|-------|--------|
| P4 | 22/22 PASS |
| P3 | 20/20 PASS |
| P2 browser | 11/11 PASS |
| P1 | PASS |

Detalle: `docs/cognitive_qa/P4_TEST_REPORT.md`

```bash
pytest tests/test_p4_goals.py -m browser
```

---

## 20. Regresión

`docs/cognitive_qa/P4_REGRESSION_REPORT.md`

- Golden v90 (seed 42, 12 ticks): `77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c` ✓
- Quality gates A–K: PASS

---

## 21. Performance

`docs/cognitive_qa/P4_PERFORMANCE_BASELINE.md`

- Parse/relevance/progress: sub-ms
- Overhead P4 << Playwright + integrated stack

---

## 22. Dependencias

- Sin LLM · sin API externa · offline Web Lab
- Playwright optional extra `[browser]` (igual que P2/P3)

---

## 23. Archivos creados

```text
nexo_qa/goals/__init__.py
nexo_qa/goals/models.py
nexo_qa/goals/parser.py
nexo_qa/goals/context.py
nexo_qa/goals/progress.py
nexo_qa/goals/relevance.py
nexo_qa/goals/runtime.py
nexo_qa/scenarios/task_definition.py
nexo_qa/scenarios/oracle.py
tests/test_p4_goals.py
tests/fixtures/web_lab/adversarial.html
configs/nexo_qa/p4_goals.yaml
artifacts/p4/preflight.json
artifacts/p4/quality_gate.json
docs/cognitive_qa/P4_*.md (14 docs)
docs/cognitive_qa/adr/ADR-0005-goal-semantics-task-context.md
P4_NEXO_COGNITIVE_QA_ENTREGA.md
```

---

## 24. Archivos modificados

```text
nexo_qa/__init__.py          → phase P4
nexo_qa/testing/__init__.py  → bind_task
nexo/prefrontal/deliberation.py → goal_relevance
nexo/core/process_executive.py → goal_relevance in BG + PFC pass-through
tests/test_p0_nexo_qa_import.py → phase assert
.github/workflows/tests.yml  → optional P4 step
```

---

## 25. Riesgos y limitaciones

`docs/cognitive_qa/P4_RISKS_AND_DEBT.md`

- Parser frágil fuera del subset documentado
- Subgoals parser-derived, no emergentes
- WM goal rehearsal mínima
- No afirmar razonamiento humano ni completion garantizada

---

## 26. Quality Gate — respuestas explícitas

| Pregunta | Respuesta |
|----------|-----------|
| ¿NEXO v90 sigue funcionando? | **YES** |
| ¿P1/P2/P3 preservados? | **YES** |
| ¿Goal declarativo? | **YES** |
| ¿Goal contiene pasos correctos? | **NO** |
| ¿TaskContext separado del oracle? | **YES** |
| ¿Oracle en decisión? | **NO** |
| ¿Intención activa? | **YES** |
| ¿Goal relevance en deliberación? | **YES** |
| ¿Percepción limitada preservada? | **YES** |
| ¿Progress por evidencia? | **YES** |
| ¿Progress por step count? | **NO** |
| ¿Recuperación posible? | **YES** (mecanismo) |
| ¿Web sobrescribe TaskGoal? | **NO** |
| ¿LLM requerido? | **NO** |
| **¿Listos para P5?** | **YES** |

---

## 27. Handoff P5

`docs/cognitive_qa/P4_HANDOFF_TO_P5.md`

**P5:** Cognitive Personas — mismo goal, distinto perfil → distinto comportamiento.

Entrada mínima para nueva sesión:

```text
repositorio + P0…P4 entregas + docs/cognitive_qa/P4_OVERVIEW.md
```

---

## 28. Uso rápido

```python
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig
from nexo_qa.browser import BrowserWorld, BrowserConfig
from nexo_qa.goals import bind_task
from nexo_qa.scenarios.task_definition import register_pro_task, REGISTER_PRO_CONTEXT
from nexo_qa.testing import bind_world

rt = IntegratedRuntime(IntegratedRuntimeConfig(seed=42, ticks=64, executive_mode="integrated"))
world = BrowserWorld(initial_url=url, config=BrowserConfig(...))
bind_task(rt, goal=register_pro_task(), task_context=REGISTER_PRO_CONTEXT, world=world)
world.start()
rt.run()
world.close()
```

---

## 29. ADR

[ADR-0005](docs/cognitive_qa/adr/ADR-0005-goal-semantics-task-context.md) — goals en `nexo_qa/`, hooks mínimos en core.

---

## 30. Principio final (P4)

> P1 dio mundos intercambiables.  
> P2 conectó la web real.  
> P3 limitó la percepción.  
> **P4 dio intención declarativa sin script.**

NEXO puede interpretar parcialmente un objetivo, equivocarse, observar falta de progreso, reconsiderar y continuar — **sin que el framework entregue el camino correcto**.
