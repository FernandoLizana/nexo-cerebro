# P2 — Browser driver protocol

`nexo_qa/browser/protocol.py` · `BrowserDriverProtocol`

| Method | Responsibility |
|--------|----------------|
| `start()` | Launch browser/context/page |
| `navigate(url)` | Allowlist check + goto |
| `snapshot()` | DOM_FAST extract → `BrowserSnapshot` |
| `execute(command)` | Low-level `BrowserCommand` |
| `close()` | Tear down context/browser/playwright |

Implementation: `PlaywrightDriver` (sync API — NEXO integrated runtime is synchronous).

Command types: `CLICK`, `FOCUS`, `TYPE`, `SELECT`, `TOGGLE`, `SCROLL`, `BACK`, `NAVIGATE`.

Results: `BrowserExecutionResult` with normalized `error_type` (`POLICY_BLOCKED`, `ELEMENT_NO_LONGER_AVAILABLE`, …).

Driver does **not** know goals, ActionSchema, or NEXO events.
