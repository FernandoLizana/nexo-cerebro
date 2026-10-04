# S15 — Real Multi-device Lab Runbook

**Status:** Voluntary scientific lab  
**Prerequisite:** S0–S14 green; Core fortress green  
**Non-goals:** Federated learning (S17); silent install; remote shell

---

## 1. Purpose

Run the same allowlisted experiment across **≥2 physical devices** owned by consenting operators, with:

- TLS transport (node ↔ coordinator)
- signed registration / heartbeats
- reproducible **experiment IDs**
- owner **kill switches** verified on each device

---

## 2. Roles

| Role | Count | Duties |
|------|------:|--------|
| Coordinator host | 1 | In-process or TLS-terminated control plane; never runs cognition / shell |
| Node devices | ≥2 | `nexo-node` with local identity keys; resource limits set by owner |

---

## 3. Pre-flight checklist

1. Each owner accepts packaging consent (S13/S14).  
2. Each device: `nexo-node start` then `nexo-node stop` (kill switch smoke).  
3. TLS certificates provisioned; **no plaintext** coordinator URL.  
4. Confirm job allowlist only — `EXECUTE_SHELL` must fail.  
5. Generate experiment id:

```bash
nexo-lab experiment-id --lab-name mylab --seed 42 --devices nodeA nodeB
```

6. In-process rehearsal (CI / laptop):

```bash
nexo-lab rehearse --seed 42 --lab-name mylab
```

---

## 4. Physical procedure (summary)

1. Start coordinator with TLS listener (operator-run; not a public open proxy).  
2. On each device: register with signed challenge; heartbeat.  
3. Dispatch **only** allowlisted jobs (`RUN_TEXTWORLD_EXPERIMENT`, `RUN_NODE_SELF_CHECK`, …).  
4. Ingest events → **quarantine** (S9); no auto-promote.  
5. Record `experiment_id`, seeds, device public keys, and traces.  
6. On any concern: `nexo-node stop` on every device.

Detailed fault cases: `docs/experiments/S15_FAULT_INJECTION.md`.

---

## 5. Acceptance

- [ ] Same seed + device set ⇒ same `experiment_id`  
- [ ] Kill switch clears in-memory private key on each device  
- [ ] Bad signature / revoke / heartbeat timeout / forbidden jobs rejected  
- [ ] Fortress tests still green  
- [ ] FL disabled  

See also: `docs/experiments/S15_CHECKLIST.md`.
