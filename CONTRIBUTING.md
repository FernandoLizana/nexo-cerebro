# CONTRIBUTING

Thanks for helping improve NEXO — an experimental distributed cognitive-agent laboratory.

## Principles

1. **Protect the Core.** Changes under `services/` / `protocols/` must not break `nexo/` determinism or `nexo_qa` fortress gates.
2. **Science over SaaS.** Do not add billing, multi-tenant product, or silent telemetry.
3. **Fail closed.** Unknown jobs, bad signatures, and silent-install flags are rejected.
4. **No consciousness claims.** Personality/drive parameters are experimental controls for synthetic agents.

## Development loop

```text
Analyze → Design → Test Core fortress → Implement one concern → Test → Document → Commit
```

```bash
python -m pip install -e ".[dev]"
python -m pytest tests/test_swarm_core_fortress.py -q
python scripts/validate_pre_release.py
```

Docker alternative: see [`docs/DOCKER_VALIDATION.md`](docs/DOCKER_VALIDATION.md).

## Branch & commits

- Prefer focused commits (one phase/concern).
- Do not commit `data/brain_state/*` noise, `data/product.db`, or `nexo_qa/product/`.
- Do not commit node private keys under `data/nexo_node*/`.

## Tests

- Swarm features: add `tests/test_sN_*.py` or extend the relevant suite.
- Static deny-lists in fortress must stay green.
- New network/shell imports in Swarm packages require explicit security review.

## Code of conduct

See [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
