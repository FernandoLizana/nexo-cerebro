# S15 — Fault injection

Faults are exercised in CI via `services.lab.faults` (in-process coordinator). Physical labs should repeat the same expectations on real TLS links.

| Fault | Expected |
|-------|----------|
| Bad heartbeat signature | Rejected |
| Heartbeat timeout | Node offline; dispatch blocked |
| Node revoke | Dispatch blocked |
| `EXECUTE_SHELL` | Rejected (not allowlisted) |

Run battery:

```bash
nexo-lab rehearse
```

The rehearsal fails if any fault case does not reject as required.
