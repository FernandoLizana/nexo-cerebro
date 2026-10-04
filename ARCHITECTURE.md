# ARCHITECTURE

NEXO is an **experimental distributed cognitive-agent laboratory**.

It does **not** claim biological consciousness, validated human psychology, or commercial multi-tenant SaaS.

## Two stacks (keep them separate)

| Stack | Location | Role |
|-------|----------|------|
| **Core** | `nexo/`, `nexo_qa/` | Deterministic cognitive runtime, scientific QA (P0–P9) |
| **Collective Swarm** | `services/`, `protocols/` | Voluntary nodes, Beings, worlds, memory, lab, learning |

**Rule:** no Swarm feature may weaken Core determinism, MessageBus locality, or scientific gates without a new golden baseline.

## Canonical docs

- GitHub overview (Flask + presence + mobile + brain): [`docs/NEXO_ARCHITECTURE.md`](docs/NEXO_ARCHITECTURE.md)
- Swarm architecture: [`docs/NEXO_SWARM_ARCHITECTURE.md`](docs/NEXO_SWARM_ARCHITECTURE.md)
- Security model: [`docs/NEXO_SWARM_SECURITY_MODEL.md`](docs/NEXO_SWARM_SECURITY_MODEL.md) · [`docs/NEXO_SECURITY.md`](docs/NEXO_SECURITY.md)
- Install / pairing: [`docs/NEXO_INSTALL.md`](docs/NEXO_INSTALL.md)
- Architecture audit (S0): [`docs/NEXO_SWARM_ARCHITECTURE_AUDIT.md`](docs/NEXO_SWARM_ARCHITECTURE_AUDIT.md)
- Master plan (S0–S17): [`docs/planes/NEXO_SWARM_MASTER_PLAN.md`](docs/planes/NEXO_SWARM_MASTER_PLAN.md)
- Cognitive lab plan: [`docs/planes/NEXO_COGNITIVE_LAB_PLAN.md`](docs/planes/NEXO_COGNITIVE_LAB_PLAN.md)

## Swarm layers (implemented S0–S17)

```text
Dashboard (read-only)     Packaging (Win/Deb)
        │
   Lab toolkit (S15)  ←→  Simulator (S11)
        │
 Coordinator (in-process control plane)
        │
 Node runtime · Being · Creature · Worlds · BIP/Events
        │
 Local memory · Experience store · Knowledge graph
        │
 Collective learning (manual) · Federated research (opt-in)
```

MessageBus stays **in-process**. Networking for physical multi-device labs is voluntary, TLS-only, and allowlisted — never remote shell.
