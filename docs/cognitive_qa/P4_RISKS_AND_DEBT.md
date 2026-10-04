# P4 — Risks and debt

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| NL parser too brittle | Medium | Document supported subset; TaskContext fills gaps |
| `premium` ↔ `pro` synonym false positive | Low | Entity match uses word boundaries where possible |
| Homeostatic `goals.updated` may interleave with task goals | Low | TaskGoalProcess re-emits each tick; last writer on same tick order-dependent |
| Autonomous Pro success not seed-guaranteed | Medium | Document as P4 mechanism demo, not KPI |
| Thin WM goal rehearsal | Low | Deferred to P5 |

## Known limitations

1. **Subgoals from parser**, not emergent deliberation
2. **No LLM** — arbitrary NL not supported
3. **Progress is ordinal**, not percentage-calibrated
4. **Loop/drift events** audit-only — no auto-recovery planner
5. **Goal abandon** status defined but not auto-triggered

## Debt register

| Item | Target phase |
|------|--------------|
| WM explicit goal tokens | P5 |
| Metacognitive recovery subgoals | P5 |
| Externalized relevance weights | P9 calibration |
| Full P4 doc set | **Closed this pass** |
| `artifacts/p4/runs/` trace store | P6 ops |

## Security

P4 does not weaken P2/P3: allowlist, selector secrecy, redaction unchanged.

## Overclaim guard

Do **not** claim: human planning, human comprehension, guaranteed task completion, or LLM-grade NLU.
