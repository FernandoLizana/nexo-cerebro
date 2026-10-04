# P4 — Task context

Implementation: `nexo_qa/goals/models.py` — `TaskContext`.

## Agent-visible fields

| Field | Purpose | Example |
|-------|---------|---------|
| `user_name` | Form fill | `"Nexo Test"` |
| `email` | Form fill | `"nexo@example.test"` |
| `desired_plan` | Constraint hint | `"Pro"` |
| `locale` | Parser bias | `"es"` |
| `extra` | Extension map | Custom slots |

Exposed to cognition via `bind_task(..., task_context=...)` and merged into parser entities/constraints.

## Test-only (never in TaskContext)

| Forbidden | Why |
|-----------|-----|
| CSS selectors | Selector secrecy |
| element_id | Internal browser identity |
| `correct_action` | Oracle leakage |
| `next_step` | Script leakage |
| `expected_path` | Planner leakage |
| Oracle module imports | ORACLE ≠ PLANNER |

## How values reach the browser

`TaskContext` → parser entities → `BrowserConfig.test_data` (via scenario wiring) → `action_mapper` type actions.

NEXO does not receive “type X into field #name” — it receives affordances from **perceived** form fields plus context values for fill text.

## Redaction

Password fields: P3 `redact_sensitive()` in perception layer. TaskContext must not embed secrets — use test placeholders only.

## Field semantics matching

Parser merges context when NL omits entities:

```text
Goal: "Completa el registro"
Context: desired_plan=Pro
→ entities.plan = "Pro"
→ constraints.must_select_plan = "Pro"
```

## Serialization

`TaskContext.agent_dict()` — safe for cognitive audit traces. Tests scan for forbidden oracle tokens (`test_task_context_leakage`).

## Config

`configs/nexo_qa/p4_goals.yaml`:

```yaml
task_context:
  user_name: "Nexo Test"
  email: "nexo@example.test"
  desired_plan: "Pro"
```

## Related

- [P4_ORACLE_SEPARATION.md](P4_ORACLE_SEPARATION.md)
- [P4_INSTRUCTION_AUTHORITY.md](P4_INSTRUCTION_AUTHORITY.md)
