# Experiments

Voluntary scientific lab runbooks for NEXO Collective Swarm.

| Doc | Purpose |
|-----|---------|
| [S15_MULTI_DEVICE_LAB.md](S15_MULTI_DEVICE_LAB.md) | ≥2-device lab procedure (TLS, allowlisted jobs) |
| [S15_FAULT_INJECTION.md](S15_FAULT_INJECTION.md) | Expected fault outcomes |
| [S15_CHECKLIST.md](S15_CHECKLIST.md) | Pre-flight acceptance checklist |

## Quick rehearsal (single machine)

```bash
nexo-lab rehearse --seed 15 --lab-name local
python -m pytest tests/test_s15_multi_device_lab.py -q
```

Federated learning research (opt-in only):

```bash
nexo-fl --enable-research --acknowledge-risks demo-round
```

Do not treat simulator or rehearsal metrics as proof of internet-scale networking.
