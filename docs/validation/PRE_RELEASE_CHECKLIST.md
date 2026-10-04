# Pre-release checklist (human + automated)

Use this before pushing `nexo-collective-swarm` to GitHub.

## Automated (required)

```bash
python scripts/validate_pre_release.py
# or
docker compose -f docker-compose.validate.yml run --rm nexo-validate
```

Expect: `ALL GATES PASSED`.

## Manual spot checks

- [ ] `nexo-node start` then `nexo-node stop` (kill switch) on a temp `--data-dir`
- [ ] `nexo-dashboard --host 127.0.0.1` refuses `0.0.0.0` via CLI
- [ ] `nexo-fl status` fails without `--enable-research --acknowledge-risks`
- [ ] `nexo-winpack /S accept-consent --i-accept-all` fails (silent install)
- [ ] No `nexo_qa/product/` or `data/product.db` on disk
- [ ] README opens with lab framing (no consciousness claims)
- [ ] `git status` has no secrets (`.pem`, `.env`, dashboard tokens)

## Security reminders

- Dashboard = loopback + token, read-only  
- Coordinator jobs fail closed  
- Experience / learning never auto-deploy to Core  
- Physical multi-device: TLS only (`docs/experiments/`)
