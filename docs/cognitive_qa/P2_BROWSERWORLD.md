# P2 — BrowserWorld

Module: `nexo_qa/browser/browser_world.py`

Implements P1 `EnvironmentProtocol`:

| Method | Role |
|--------|------|
| `percepts_for_agent` | DOM_FAST → `(modality, salience, embedding)` |
| `available_actions` / `action_schemas` | Dynamic catalog per snapshot |
| `action_info` | Scoring hints for integrated BG |
| `apply_action` | Resolve `web:*` id → `BrowserCommand` → driver |

Lifecycle: `start` → `reset` / ticks → `close`. Context manager supported.

Bind pattern (unchanged from P1):

```python
rt = IntegratedRuntime(...)
bind_world(rt, BrowserWorld(initial_url=url, config=cfg))
world.start()
rt.run()
world.close()
```

BrowserWorld is **dumb**: perceives, lists actions, executes, returns outcomes. No goal planning, no step scripts, no correction of NEXO choices.

Trace events (internal): `BROWSER_SNAPSHOT`, `WEB_ACTIONS_AVAILABLE`, `BROWSER_COMMAND`, `BROWSER_RESULT`, `WEB_OUTCOME`.
