# SECURITY

NEXO nodes are **voluntarily installed** for scientific participation.

Full model: [`docs/NEXO_SWARM_SECURITY_MODEL.md`](docs/NEXO_SWARM_SECURITY_MODEL.md) · hardening checklist: [`docs/NEXO_SECURITY.md`](docs/NEXO_SECURITY.md).

## Hard prohibitions

- Network scanning / host discovery
- Self-replication / worm-like propagation
- Silent or hidden installation
- Remote shell / arbitrary command execution
- Hidden persistence / anti-uninstall tricks
- Credential harvesting / keylogging
- Filesystem crawling / browser-history collection
- Disabling antivirus / privilege escalation

**Only** allowlisted NEXO jobs may run.

## Owner controls

1. Explicit install + consent (Windows/Debian packaging)
2. Resource limits (`ResourceGovernor`)
3. Kill switch: `nexo-node stop` / `NEXO-Node.exe stop`
4. Clean uninstall without fighting persistence
5. Private keys never leave the device
6. Manual updates by default; FL research is **opt-in** (S17)

## Transport & trust

- TLS required for physical multi-device labs (no plaintext)
- Ed25519 node identity; reject bad signatures
- Coordinator can revoke nodes; events stay quarantined until explicit promote
- Dashboard is loopback + token, read-only (no job injection)

## Reporting

Prefer responsible disclosure to maintainers. Do not file public issues that include private keys, consent tokens, or live lab credentials.

## Pre-push validation

```bash
python scripts/validate_pre_release.py
# or isolated:
docker compose -f docker-compose.validate.yml run --rm nexo-validate
```

See [`docs/validation/PRE_RELEASE_CHECKLIST.md`](docs/validation/PRE_RELEASE_CHECKLIST.md).
