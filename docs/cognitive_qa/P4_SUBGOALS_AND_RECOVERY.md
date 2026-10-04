# P4 — Subgoals and recovery

## Subgoals

### Source (P4)

Subgoals are **parser-derived semantic phases**, not scenario step tables:

```text
localizar_inicio → completar_informacion → seleccionar_plan → confirmar
```

`TaskGoalProcess` advances `active_subgoal` from **progress evidence** (URL phase), not from oracle step index.

### Not in P4

- Emergent subgoals from full deliberation/planning
- LLM-generated plans
- Hardcoded `REGISTER_PRO → [click, type, ...]` maps

### Future (P5+)

Metacognitive recovery subgoals (`re-examine scene`, `scroll`, `go back`) should emerge from cognitive core when stagnation detected — P4 only **detects** stagnation.

## Recovery

### Wrong choice without auto-correct

Test flow: on `plan.html`, NEXO may activate Basic → navigates to `summary.html?plan=basic`. Framework does **not** rewind or inject correct action. Progress re-evaluates from new URL.

### Stagnation / loop detection

`LoopDetector` in `nexo_qa/goals/runtime.py`:

| Signal | Condition |
|--------|-----------|
| `goal.behavior_loop` | Same action repeated in window |
| `goal.drift` | Many actions, same URL (stagnation) |

Events are **audit only** — no automatic correction in P4.

### Blocked goal

Policy-blocked navigation → `GoalProgress.status = BLOCKED`. Security unchanged — goal cannot bypass allowlist.

## Recovery semantics (conceptual success path)

```text
wrong action → new outcome → progress re-evaluated → relevance shifts → NEXO may select different action
```

Not guaranteed in all seeds; mechanism is present.

## Related tests

- `test_wrong_choice_recovery_no_auto_correct`
- `test_loop_detection`
- `test_goal_drift_detection`
- `test_blocked_goal_policy`
