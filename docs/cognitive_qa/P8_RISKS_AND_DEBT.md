# P8 — Risks and Debt

| Risk | Mitigation |
|------|------------|
| Browser chaos not in default CI | MockWorld + HTML fixtures; BrowserWorld opt-in |
| Combined perturbations | Max 2 deferred to config guard |
| Wall-clock vs cognitive time | Documented; ticks preferred in CI |

Deferred: full BrowserWorld injection hooks, bootstrap CIs on deltas.
