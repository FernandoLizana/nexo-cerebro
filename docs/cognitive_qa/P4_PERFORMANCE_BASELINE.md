# P4 — Performance baseline

Measured on developer machine (Windows, Python 3.11, Web Lab offline).

## Unit operations (approximate)

| Operation | Avg time | Notes |
|-----------|----------|-------|
| `parse_goal()` | < 0.1 ms | Pure Python regex |
| `goal_relevance_map()` (10 actions) | < 0.2 ms | Token overlap |
| `evaluate_progress()` | < 0.05 ms | URL parse |
| `TaskGoalProcess.step()` | < 1 ms | Excluding world I/O |

## Integrated task run

| Scenario | Ticks | Wall time | Overhead vs P3-only |
|----------|-------|-----------|---------------------|
| `register_pro_autonomous` | 96 | ~15–25 s | Dominated by Playwright + full integrated stack |
| Goal events per tick | 1–3 | negligible vs perception | `goal.progress`, `goals.updated`, optional `goal.relevance` |

## P4-specific overhead

Goal parsing + relevance per tick adds **sub-millisecond** Python work. No orders-of-magnitude regression vs P3 web loop.

Alert threshold from prompt: >10× tick cost on simple pages — **not observed**.

## Artifacts

See `artifacts/p4/quality_gate.json` for captured preflight metadata.

## Reproduce

```bash
python -m pytest tests/test_p4_goals.py -q -m browser --durations=10
```

Performance gate: **PASS** (no premature optimization required).
