# P7 — Risks and Debt

| Risk | Mitigation |
|------|------------|
| Plan hash includes artifact_path | Use consistent artifact_root; path is storage not identity |
| Browser population cost | Default trace_fixture in CI; retention policies |
| Small-N overinterpretation | `INSUFFICIENT_SAMPLE` status, explicit denominators |
| Cartesian stress explosion | One-factor-at-a-time default; run count guards |

Deferred: multi-factor stress grids, bootstrap CIs, distributed runner, browser backend in CI.
