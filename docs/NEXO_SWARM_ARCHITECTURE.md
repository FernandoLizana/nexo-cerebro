# NEXO Collective Swarm — Architecture

**Status:** S0–S17 implemented on branch `nexo-collective-swarm`  
**Companion:** `docs/NEXO_SWARM_ARCHITECTURE_AUDIT.md`, `docs/NEXO_SWARM_SECURITY_MODEL.md`, `docs/planes/NEXO_SWARM_MASTER_PLAN.md`

---

## 1. Mission

NEXO is an **experimental distributed cognitive-agent laboratory**.

It studies:

- synthetic cognitive agents (Beings);
- collective intelligence and shared experience;
- distributed memory and knowledge candidates;
- inter-agent learning and relationship dynamics;
- emergent social patterns in controlled worlds.

It does **not** claim biological consciousness, validated human psychology, or commercial SaaS multi-tenancy.

---

## 2. Layered collective intelligence (not “one giant Transformer”)

Do **not** shard Transformer layers across untrusted machines.

```text
                  NEXO COLLECTIVE BRAIN

                     Global Memory
                          │
                     Knowledge Graph
                          │
                   Experience Engine
                          │
                     Learning Engine
                          │
             ┌────────────┼────────────┐
             │            │            │
           Node A       Node B       Node C
             │            │            │
          Being A       Being B      Animal C
             │            │            │
             └──────── interaction ────┘
```

| Layer | Role | Core reuse |
|-------|------|------------|
| **Local Intelligence** | Perception, deliberation, action, local memory | `IntegratedRuntime` + PFC/BG/WM/hippo |
| **Shared Experience** | Signed events from Being interactions / experiments | analysis, failures, reporting |
| **Global Memory** | Quarantined → promoted knowledge store | **new** (consent + validation pipeline) |
| **Knowledge Graph** | Abstract interfaces first | connectome is **local only** |
| **Optional Federated Learning** | Late phase; sandbox + rollback | local TD only today |

---

## 3. Separation of planes

```text
┌─────────────────────────────────────────────────────────┐
│  SCIENTIFIC CORE (protected)                            │
│  nexo/ + nexo_qa harness (MockWorld, BrowserWorld, …)   │
│  MessageBus = in-process ONLY                           │
└──────────────────────────▲──────────────────────────────┘
                           │ bind_world / bind_persona / traces
┌──────────────────────────┴──────────────────────────────┐
│  SWARM PLANE (new, outside Core)                        │
│  services/node  ·  services/coordinator  ·  protocols   │
│  TLS · node identity · allowlisted jobs · events        │
└─────────────────────────────────────────────────────────┘
```

**Rule:** Swarm adapters call Core through narrow, tested APIs. Core never imports Swarm networking.

---

## 4. NEXO Node (design)

Multiplatform voluntary runtime (later: Windows EXE, Debian DEB).

Identity (private key **never leaves device**):

- `node_id`, `public_key`, `node_name`
- `hardware_profile`, `capability_profile`, `software_version`, `created_at`

Protocols (signed over TLS):

`registration` · `authentication` · `heartbeat` · `capabilities` · `job reception` · `event submission` · `interaction` · `disconnect` · `reconnect` · `revocation`

Capability tiers (approximate):

| Tier | Name | Intent |
|------|------|--------|
| 0 | MICRO | Creature Engine / FSM only |
| 1 | LIGHT | Small local models optional |
| 2 | STANDARD | TextWorld + modest Being |
| 3 | ADVANCED | BrowserWorld experiments |
| 4 | RESEARCH | Heavier local budgets (explicit opt-in) |

`ResourceGovernor` enforces user limits (CPU%, RAM, GPU on/off, schedules, battery mode). Kill switch: **STOP NEXO NODE** → stop jobs, close connections, save state, exit workers — no anti-uninstall persistence.

---

## 5. Beings

Persistent experimental entities: `HUMANOID` | `ANIMAL` | `CREATURE` | `EXPERIMENTAL`.

Versioned split storage (avoid giant `being.json`):

| Part | Contents |
|------|----------|
| IDENTITY | id, name, species, archetype, creator_node |
| MEMORY | episodic / semantic / relationships / summaries |
| STATE | drives, temporary affect, working memory |
| COGNITIVE CONFIG | model/budget/parameters (experimental) |

**Creature Engine (Tier 0–1):** behavior trees, FSM, utility AI, associative memory, small embeddings, RL signals — **practically without LLM**.

Personality sliders are **experimental parameters**, not validated human psychology.

Evolution must distinguish:

`CORE PERSONALITY` · `LEARNED BEHAVIOR` · `MEMORY` · `RELATIONSHIPS` · `TEMPORARY STATE`

with bounded drift for scientific questions (divergence, convergence, specialization, social hubs).

---

## 6. Interaction & events

**Being Interaction Protocol** (initial):  
`MESSAGE` `OBSERVE` `REQUEST` `OFFER` `HELP` `REJECT` `PLAY` `TEACH` `ASK` `SHARE_MEMORY` `SHARE_DISCOVERY`

Each interaction emits a signed event. **Never** auto-upload private user chats — only NEXO world interactions.

**NEXO Event Protocol** (versioned, timestamped, signed):  
`NODE_CONNECTED` `BEING_CREATED` `BEING_INTERACTION` `BEING_LEARNED` `BEING_FAILED` `BEING_DISCOVERED` `EXPERIMENT_STARTED` `EXPERIMENT_COMPLETED` `MEMORY_CREATED` `MEMORY_RECALLED` `KNOWLEDGE_CANDIDATE`

---

## 7. Memory pipelines

### Local (per Being)

```text
memory/
  episodic/
  semantic/
  relationships/
  summaries/
```

Fields: `importance`, `confidence`, `timestamp`, `source`, `decay`, `recall_count`.

### Global (network)

```text
RAW EXPERIENCE
  → VALIDATION → QUARANTINE → DEDUPLICATION
  → CROSS-NODE COMPARISON → CONFIDENCE
  → CANDIDATE KNOWLEDGE → PROMOTED KNOWLEDGE
```

**Never:** event received ⇒ immediate global truth.

---

## 8. Worlds

`WorldAdapter` interface; first implementation **TextWorld** (cheap, reproducible).  
Reuse existing **BrowserWorld / Web Lab** behind policy allowlists. Future: GridWorld, SocialWorld, GameWorld.

---

## 9. Coordinator

`services/coordinator/` (future):

- node registry, heartbeats, capability registry
- experiment scheduler, interaction router
- event ingestion, network telemetry

Coordinator **coordinates** — it does **not** run fundamental cognition.

Job allowlist only, e.g.:

- `RUN_TEXTWORLD_EXPERIMENT`
- `RUN_BEING_INTERACTION`
- `RUN_BROWSERWORLD_EXPERIMENT`

**Not:** `EXECUTE_SHELL("…")`.

---

## 10. Swarm Simulator (before real internet)

Event-driven logical nodes (10 → 10 000) **without** 10 000 OS processes. Study load, throughput, memory growth, scheduler, social graphs, knowledge propagation.

---

## 11. Observability

Local scientific dashboard: nodes, beings, interactions, experiments, memories, knowledge candidates/promoted, failures, **live network graph**.

Later: **NEXO BRAIN** visualization as a system diagram — **not** a claim of biological neural tissue.

---

## 12. Learning phases (global)

| Phase | Content |
|-------|---------|
| A | Shared experiences, memories, KG, retrieval |
| B | Distillation experiments |
| C | Optional federated learning |
| D | Optional LoRA/adapter aggregation |

Any parameter learning: evaluation → sandbox → comparison → rollback. **Never** auto-deploy a fresh model to the whole network.

---

## 13. Core protection contract

1. Fortress tests gate Core imports, MessageBus locality, policy defaults, phase markers.  
2. Swarm packages live under `services/` / `nexo_swarm/` — Core does not depend on them.  
3. Dirty SaaS trees must not define “truth”; HEAD + golden baseline do.  
4. One phase at a time: analyze → design → test Core → implement → test → document → commit.
