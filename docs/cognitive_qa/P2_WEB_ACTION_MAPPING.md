# P2 — Web action mapping

`nexo_qa/browser/action_mapper.py`

## Snapshot → ActionSchema

Examples from Web Lab:

- `web:activate:0001` — label `activate "Comenzar"`, affordance `selectable`
- `web:focus:0002` — label `focus "Nombre"`
- `web:type:0003` — label `type into "Nombre"` (text from `config.test_data`)
- `web:navigate:000N` — `go back`
- `web:scroll:000N` — `scroll down`

## ActionSchema.id → BrowserCommand (internal)

Stored in `BrowserWorld._commands` — never serialized to cognition.

Example:

```text
ActionSchema id=web:activate:0001
BrowserCommand CLICK element_id=web:e:0001
Driver locator testid=start-btn (internal)
```

Reversible within one snapshot generation cycle; registry invalidated on navigation/DOM change.
