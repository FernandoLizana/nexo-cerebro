# P2 — Web Lab

Root: `tests/fixtures/web_lab/`

Server: `nexo_qa.testing.web_lab_server.WebLabServer` (stdlib `ThreadingHTTPServer`)

## Flow

1. `index.html` — Bienvenido + **Comenzar**
2. `name.html` — Nombre input + **Continuar**
3. `plan.html` — **Básico** / **Pro**
4. `summary.html` — **Confirmar**
5. `success.html` — completion (`?plan=`)

## Goal (agent-facing documentation only)

`Completar el flujo de demostración usando el plan Pro.`

## Test oracle (NOT agent knowledge)

- Success: URL ends with `/success.html`
- Pro success: query `plan=pro`

## Test data (for TYPE actions only)

```yaml
name: Nexo Test
email: nexo@example.test
```

Not a step script.

Config: `configs/nexo_qa/browser_lab.yaml`
