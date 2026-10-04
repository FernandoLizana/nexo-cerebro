# P4 — Goal parser

Implementation: `nexo_qa/goals/parser.py` — `parse_goal()`.

## Design constraints

- **No LLM** — regex, keyword domains, small synonym map
- **No step extraction** — outputs entities, constraints, semantic subgoals only
- **ES + EN** — basic patterns for Web Lab and common QA phrases
- **ENGINEERING DEFAULT** — not human-calibrated NLU

## Pipeline

```text
raw description (NL)
  ↓ normalize (lowercase, collapse whitespace)
  ↓ detect domain (registration | plan_selection | find_pricing | navigation | general)
  ↓ extract entities (plan, name, email from text + TaskContext)
  ↓ build constraints (must_select_plan, must_use_email, must_not_leave_allowed_origin)
  ↓ derive semantic subgoals (from domain — not scenario tables)
  ↓ Goal(PENDING)
```

## Supported goal examples

| Input | Domain | Entities |
|-------|--------|----------|
| "Completa el registro y selecciona el plan Pro." | `registration` | `plan=Pro` |
| "Selecciona el plan Pro." | `plan_selection` | `plan=Pro` |
| "Encuentra la sección de precios." | `find_pricing` | — |
| "Vuelve a la página anterior." | `navigation` | — |

## Synonym map (generic)

| Canonical | Variants |
|-----------|----------|
| register | registro, sign up, crear cuenta |
| plan | subscription, precio, pricing |
| pro | premium |
| basic | básico, gratis, free |
| confirm | confirmar, finalizar, completar |

**Prohibited:** Web-Lab-specific strings like `"Click Comenzar"` baked into parser logic.

## Subgoal derivation

`_derive_subgoals(domain, entities)` returns semantic phase names:

- `registration` → `localizar_inicio`, `completar_informacion`, `seleccionar_plan`, `confirmar`
- `find_pricing` → `explorar_sitio`, `localizar_seccion_precios`

These are **not** ordered step scripts — they inform `active_subgoal` and relevance, not forced action sequences.

## Forbidden output check

`goal_contains_steps(goal_dict)` scans for: `expected_actions`, `step_sequence`, `selectors`, `correct_action`, `next_step`.

## Extension (P5+)

Optional LLM adapter may wrap `parse_goal` — must not become mandatory for CI/offline Web Lab.
