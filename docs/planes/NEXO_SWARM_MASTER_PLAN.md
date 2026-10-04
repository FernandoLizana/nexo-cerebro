# NEXO Collective Swarm — Master Plan

**Branch:** `nexo-collective-swarm` (from `c5892c3e` / Cognitive Lab line)  
**Rule:** Analyze → Design → Test Core → Implement **one** phase → Test → Document → Commit  
**Do not** auto-advance ten phases. **Do not** implement multi-machine networking before S2+ and Core fortress green.

Related:

- `docs/NEXO_SWARM_ARCHITECTURE_AUDIT.md`
- `docs/NEXO_SWARM_ARCHITECTURE.md`
- `docs/NEXO_SWARM_SECURITY_MODEL.md`
- `docs/planes/NEXO_COGNITIVE_LAB_PLAN.md` (prior scientific reframe)

---

## Development rule (non-negotiable)

```text
PROTECT THE CORE.
No Swarm feature may weaken IntegratedRuntime determinism,
trajectory integrity, MessageBus locality, or P0–P9 scientific gates
without an explicit new golden baseline and review.
```

---

## Phase index

| Phase | Name | Implement now? |
|-------|------|----------------|
| **S0** | Core Audit | Done |
| **S1** | Core Test Fortress | Done |
| S2 | Node Runtime | Done |
| S3 | Being Model | Done |
| S4 | Creature Engine | Done |
| S5 | TextWorld | Done |
| S6 | Interaction Protocol | Done |
| S7 | Coordinator | Done |
| S8 | Local Memory | Done |
| S9 | Global Experience Store | Done |
| S10 | Knowledge Graph | Done |
| S11 | Swarm Simulator | Done |
| S12 | Dashboard | Done |
| S13 | Windows EXE | Done |
| S14 | Debian DEB | Done |
| S15 | Real Multi-device Lab | Done |
| S16 | Collective Learning | Done |
| S17 | Federated Learning Research | Done |

---

## S0 — Core Audit

### OBJECTIVE

Inventory `brain/`, `nexo/`, `nexo_qa/` (P0–P9), classify KEEP/REFACTOR/ARCHIVE/REMOVE/UNKNOWN, identify Critical Core C1–C16, coupling/security risks, and freeze a golden baseline **without modifying Core cognition**.

### ARCHITECTURE

Read-only analysis + documentation plane. No Swarm packages. No TLS. No node processes.

### FILES

| Path | Role |
|------|------|
| `docs/NEXO_SWARM_ARCHITECTURE_AUDIT.md` | Classification + C1–C16 + risks |
| `docs/NEXO_SWARM_ARCHITECTURE.md` | Target layered design |
| `docs/NEXO_SWARM_SECURITY_MODEL.md` | Prohibitions + allowlist model |
| `docs/planes/NEXO_SWARM_MASTER_PLAN.md` | This roadmap |
| `artifacts/swarm/GOLDEN_BASELINE.json` | Machine-readable baseline |
| `artifacts/swarm/core_regression_stdout.txt` | Pytest transcript |

### RISKS

| Risk | Mitigation |
|------|------------|
| Dirty working tree (SaaS leftovers, untracked P1 triad) | Document; do not commit SaaS; treat HEAD as source of truth |
| Incomplete P1 commit (schema files missing from git) | Flag as S1 blocker |
| Shadow imports / markers | Fix **test hygiene only** in S0/S1 |

### TESTS

Run existing `tests/` suite; record pass/fail honestly.

### ACCEPTANCE CRITERIA

- [x] Audit document with KEEP/REFACTOR/ARCHIVE/REMOVE/UNKNOWN  
- [x] Critical Core C1–C16 listed  
- [x] Architecture + security design docs exist  
- [x] Master plan S0–S17 outlined  
- [x] No multi-machine networking implemented  
- [x] Core deliberation / runtime logic not rewritten for Swarm features  
- [x] Golden baseline artifact written (`artifacts/swarm/GOLDEN_BASELINE.json`: **155 passed / 2 failed** P0–P9+fortress, browser deselected; supplemental integrated smoke **30 passed**)  

---

## S1 — Core Test Fortress

### OBJECTIVE

Protect Critical Core with regression / fortress tests so future Swarm code cannot silently break science. Complete or explicitly quarantine incomplete P1 contract debt.

### ARCHITECTURE

```text
tests/test_swarm_core_fortress.py  →  locks imports, MessageBus locality,
                                      phase markers, PFC signature debt,
                                      BrowserPolicy defaults, seed helpers
pyproject.toml markers + conftest   →  test hygiene (not cognition)
```

Optional follow-up (still S1, **before** S2):

1. Commit ActionSchema triad if contents match P1 docs/tests.  
2. Migrate `PrefrontalDeliberator.run` to accept `action_schemas` (Core change — needs new golden if trajectory shifts).  
3. Expand fortress: trajectory_hash smoke, failure taxonomy version pin, population `plan_hash` pin.

### FILES

| Path | Role |
|------|------|
| `tests/test_swarm_core_fortress.py` | Fortress battery |
| `tests/conftest.py` | Prefer project `nexo_qa` |
| `pyproject.toml` | Register `browser` marker |
| `nexo/core/action_schema.py` (+ protocol/adapter) | **S1 completion** — track + wire (not started as behavior change in first delivery) |
| `nexo/prefrontal/deliberation.py` | **S1 completion** — schema-driven PFC |

### RISKS

| Risk | Mitigation |
|------|------------|
| “Fixing” PFC changes RoomWorld trajectories | Separate golden; compare hash before/after |
| Committing incomplete untracked files | Diff against P1 docs + `tests/test_p1_*` first |
| Expanding scope into networking | Hard stop: no `services/` yet |

### TESTS

- Fortress unit tests (always on)  
- Full `tests/` regression  
- Property: seed helpers deterministic  
- Static: MessageBus source has no network imports  

### ACCEPTANCE CRITERIA

- [x] Fortress suite exists and covers MessageBus locality + phase + imports  
- [x] `browser` marker registered; `nexo_qa` shadow package removed from tests  
- [x] Clean tree includes ActionSchema triad (tracked modules)  
- [x] PFC accepts `action_schemas`; P1 environment contract tests green  
- [x] `GOLDEN_BASELINE.json` updated (**157 passed / 0 failed**, browser deselected)  
- [x] No Swarm network code  

---

## S2 — Node Runtime

**OBJECTIVE:** Local voluntary runtime with Ed25519 identity, capability tiers, ResourceGovernor, allowlisted jobs, and kill switch — **no networking**.

**ARCHITECTURE:** `services/node/` outside Core; Core remains a library. Private key stays on disk under the owner data dir and is never printed by CLI/status.

**FILES:**

| Path | Role |
|------|------|
| `services/node/identity.py` | Ed25519 keypair + `node_id` |
| `services/node/capability.py` | Hardware/capability profile + tiers 0–4 |
| `services/node/governor.py` | THROTTLE / PAUSE / TERMINATE_JOB |
| `services/node/jobs.py` | Fail-closed job allowlist |
| `services/node/runtime.py` | Start / stop / kill switch |
| `services/node/cli.py` | `nexo-node` CLI |
| `tests/test_s2_node_runtime.py` | S2 acceptance tests |

**RISKS:** Accidental MessageBus networking (mitigated: static scan + `networking_enabled: false`); over-consuming host (governor limits).

**TESTS:** Identity round-trip + sign/verify; governor actions; allowlist rejects `EXECUTE_SHELL`; kill switch clears in-memory private key; no `socket`/`subprocess` imports in node package.

**ACCEPTANCE CRITERIA:**

- [x] Node starts/stops locally via CLI  
- [x] Private key never printed in status/self-check JSON  
- [x] Job allowlist fail-closed  
- [x] ResourceGovernor throttle/pause/terminate  
- [x] Core fortress + Cognitive QA still green (**163 passed** with S2 tests)  
- [x] No coordinator / TLS client yet  

---

## S3 — Being Model

**OBJECTIVE:** Versioned Being with split IDENTITY / MEMORY / STATE / COGNITIVE CONFIG; local Character Creator CLI.

**ARCHITECTURE:** `services/being/` on the node data plane; experimental personality sliders with explicit non-human disclaimer; no networking.

**FILES:**

| Path | Role |
|------|------|
| `services/being/models.py` | Species, personality, layers |
| `services/being/store.py` | Split filesystem persistence |
| `services/being/creator.py` | Character Creator API |
| `services/being/cli.py` | `nexo-being` CLI |
| `services/being/validation.py` | Bounds / format checks |
| `schemas/being/being-v1.json` | Format contract |
| `tests/test_s3_being_model.py` | S3 tests |

**RISKS:** Giant monolith JSON (mitigated by split store); psychology claims (disclaimer + rejected human labels).

**TESTS:** Create/reload; trait bounds; animal defaults without LLM; node `CREATE_BEING` / `LIST_BEINGS` jobs.

**ACCEPTANCE CRITERIA:**

- [x] Create/load Being offline  
- [x] Split files (no sole `being.json`)  
- [x] Experimental disclaimer present  
- [x] S2/Core fortress still green  

---

## S4 — Creature Engine

**OBJECTIVE:** Low-tier animals/creatures run without LLM via FSM + utility AI + associative memory.

**ARCHITECTURE:** `services/creature/` consumes Being state; deterministic seeded ticks; refuse `use_llm=True`.

**FILES:**

| Path | Role |
|------|------|
| `services/creature/fsm.py` | States + legal transitions |
| `services/creature/utility.py` | Utility AI scoring |
| `services/creature/memory.py` | Associative memory |
| `services/creature/engine.py` | Tick loop |
| `services/creature/cli.py` | `nexo-creature` CLI |
| `tests/test_s4_creature_engine.py` | Determinism + dynamics |

**RISKS:** Feature creep into LLM path (hard refuse); overclaiming ethology (disclaimer via Being).

**TESTS:** Deterministic trajectories; hunger/energy bounds; no LLM imports; node `RUN_CREATURE_SIMULATION`.

**ACCEPTANCE CRITERIA:**

- [x] Tier-0 style creature ticks without LLM  
- [x] Deterministic under seed  
- [x] Governor-compatible allowlisted job  
- [x] Core fortress still green  

---

## S5 — TextWorld

**OBJECTIVE:** First `WorldAdapter` — cheap, reproducible multi-Being text arena.

**ARCHITECTURE:** `services/worlds/textworld/` with EnvironmentProtocol `AgentView`; seeded ticks; local BEING_INTERACTION events only.

**FILES:**

| Path | Role |
|------|------|
| `services/worlds/adapter.py` | WorldAdapter interface |
| `services/worlds/textworld/world.py` | TextWorld + AgentView |
| `services/worlds/textworld/events.py` | Interaction / world events |
| `services/worlds/textworld/runner.py` | Seeded experiment runner |
| `services/worlds/textworld/cli.py` | `nexo-textworld` CLI |
| `tests/test_s5_textworld.py` | Replay + protocol + job tests |

**RISKS:** Diverging from MockWorld (mitigated: EnvironmentProtocol view + action_schemas_for).

**TESTS:** Identical fingerprints under same seed; interaction events; node `RUN_TEXTWORLD_EXPERIMENT`.

**ACCEPTANCE CRITERIA:**

- [x] Two Beings, same seed → identical traces  
- [x] Offline only  
- [x] Core fortress still green  

---

## S6 — Interaction Protocol

**OBJECTIVE:** Formal Being Interaction Protocol (BIP) + NEXO Event Protocol codecs.

**ARCHITECTURE:** `protocols/` outside Core; TextWorld emits only allowlisted events; privacy filter rejects private user chat fields. Signing reserved (`signature_hex`) for later.

**FILES:**

| Path | Role |
|------|------|
| `protocols/being_interaction/codec.py` | BIP encode/decode |
| `protocols/being_interaction/privacy.py` | Context sanitizer |
| `protocols/events/codec.py` | Event encode/decode |
| `services/worlds/textworld/events.py` | Adapter to formal codecs |
| `tests/test_s6_interaction_protocol.py` | Round-trip + privacy |

**RISKS:** Leaking private user data (mitigated: PrivacyViolation on forbidden keys).

**TESTS:** Unknown kinds rejected; user_chat blocked; TextWorld interactions decode as BIP.

**ACCEPTANCE CRITERIA:**

- [x] Only allowlisted interaction kinds serialize  
- [x] Privacy filter enforced  
- [x] TextWorld still reproducible  

---

## S7 — Coordinator

**OBJECTIVE:** In-process control plane — node registry, signed heartbeats, allowlisted job queue, quarantined event ingest.

**ARCHITECTURE:** `services/coordinator/` — **no cognition, no sockets, no shell**. TLS multi-device deferred to S15.

**FILES:**

| Path | Role |
|------|------|
| `services/coordinator/service.py` | Coordinator facade |
| `services/coordinator/registry.py` | Register / revoke / online |
| `services/coordinator/auth.py` | Ed25519 verify helpers |
| `services/coordinator/jobs.py` | Allowlisted job router |
| `services/coordinator/events.py` | Quarantine ingest |
| `services/coordinator/cli.py` | Local demo CLI |
| `tests/test_s7_coordinator.py` | Revoke / timeout / deny jobs |

**RISKS:** Becoming a remote shell (mitigated: reuse node allowlist; static import scan).

**TESTS:** Unknown/forbidden jobs rejected; revoke blocks dispatch; heartbeat timeout offline; events quarantined.

**ACCEPTANCE CRITERIA:**

- [x] Single node can register + heartbeat  
- [x] Jobs fail closed  
- [x] Core untouched / no networking  

---

## S8 — Local Memory

**OBJECTIVE:** Per-Being episodic / semantic / relationship / summary stores with importance, decay, and recall_count — without wholesale LLM prompt stuffing.

**ARCHITECTURE:** `services/memory/local/` rooted at ``<beings_root>/<being_id>/memory/`` (same tree as BeingStore). Individual JSON files per record; `index.json` rebuilt for Being `MemoryBundle` compatibility. Prompt path is ranked + char-budgeted only.

**FILES:**

| Path | Role |
|------|------|
| `services/memory/local/models.py` | Entry + relationship models |
| `services/memory/local/store.py` | Disk store, decay, recall |
| `services/memory/local/recall.py` | Rank / hard caps / policy errors |
| `services/memory/local/cli.py` | `nexo-memory` CLI |
| `tests/test_s8_local_memory.py` | Persist / decay / isolation / anti-dump |

**RISKS:** Prompt-stuffing everything (mitigated: `HARD_RECALL_CAP`, `MAX_PROMPT_CHARS`, `export_for_science(for_llm=True)` refused).

**TESTS:** Restart persistence; importance slows decay; recall_count bumps; Being A ≠ Being B; wholesale LLM dump rejected.

**ACCEPTANCE CRITERIA:**

- [x] Memory survives restart  
- [x] Not dumped wholesale into LLM context  
- [x] Isolation between Beings  
- [x] Core untouched / no networking in memory package  

---

## S9 — Global Experience Store

**OBJECTIVE:** Quarantine → validate → explicit promote pipeline for shared experience candidates (never auto-truth).

**ARCHITECTURE:** Append-only disk store under `services/experience/`. Ed25519 signatures on submissions. Validation can mark VALIDATED/REJECTED but **never** PROMOTED. Promotion requires an explicit call + verified signature + confidence score.

**FILES:**

| Path | Role |
|------|------|
| `services/experience/models.py` | Candidate + status enum |
| `services/experience/signing.py` | Canonical experience message |
| `services/experience/validate.py` | Schema/signature workers |
| `services/experience/store.py` | Quarantine/validated/rejected/promoted dirs |
| `services/experience/service.py` | Facade (`ingest` / `validate` / `promote`) |
| `services/experience/cli.py` | `nexo-experience` |
| `tests/test_s9_experience_store.py` | Signature / no auto-promote |

**RISKS:** Poisoning; immediate “truth” (mitigated: quarantine default; bad sig → REJECTED; promote explicit only).

**TESTS:** Bad signature rejected; validate does not promote; explicit promote yields confidence; package has no sockets/shell.

**ACCEPTANCE CRITERIA:**

- [x] End-to-end candidate knowledge with confidence score  
- [x] Quarantine never auto-promotes  
- [x] Bad signature rejected  
- [x] Core untouched  

---

## S10 — Knowledge Graph

**OBJECTIVE:** Abstract KG interfaces (Being, Node, Experiment, Concept, …) with allowlisted relations.

**ARCHITECTURE:** Interface-first (`KnowledgeGraph` Protocol); default `InMemoryKnowledgeGraph` + optional JSON persistence. **No Neo4j required.**

**FILES:**

| Path | Role |
|------|------|
| `services/knowledge/types.py` | NodeKind / EdgeRelation allowlists |
| `services/knowledge/models.py` | GraphNode / GraphEdge |
| `services/knowledge/protocol.py` | Backend contract |
| `services/knowledge/memory.py` | In-memory backend |
| `services/knowledge/service.py` | Helpers for core relations |
| `services/knowledge/cli.py` | `nexo-knowledge` |
| `tests/test_s10_knowledge_graph.py` | Contract + relation tests |

**RISKS:** Premature graph DB lock-in (mitigated: Protocol + in-memory only in S10).

**TESTS:** `INTERACTED_WITH` / `SUPPORTS` / `CONTRADICTS`; protocol satisfaction; no neo4j imports.

**ACCEPTANCE CRITERIA:**

- [x] Record core relations without Neo4j  
- [x] Pluggable interface for later backends  
- [x] Core untouched  

---

## S11 — Swarm Simulator

**OBJECTIVE:** Event-driven logical nodes (10→10 000) in one process — study load before any internet lab.

**ARCHITECTURE:** Discrete-event queue + shared `SimClock`; ring/random topology; interactions feed in-memory KG. **No sockets. No OS process per node.**

**FILES:**

| Path | Role |
|------|------|
| `services/simulator/clock.py` | Shared logical clock |
| `services/simulator/events.py` | SimEvent kinds |
| `services/simulator/node.py` | LogicalNode |
| `services/simulator/engine.py` | DiscreteEventSimulator |
| `services/simulator/metrics.py` | Throughput / memory / social stats + load curves |
| `services/simulator/cli.py` | `nexo-simulator` |
| `docs/NEXO_SWARM_SIMULATOR_LOAD_CURVES.md` | Documented envelopes |
| `tests/test_s11_swarm_simulator.py` | Budgets + reproducibility |

**RISKS:** Confusing sim metrics with real network proof (mitigated: explicit disclaimer + `networking_enabled: false`).

**TESTS:** Memory budget; social degree stats; load curve table; no socket imports; seed reproducibility.

**ACCEPTANCE CRITERIA:**

- [x] Documented load curves before internet lab  
- [x] Throughput / memory budgets reported  
- [x] Social graph stats from interactions  
- [x] Core untouched  

---

## S12 — Dashboard

**OBJECTIVE:** Local scientific dashboard + live network graph visualization.

**ARCHITECTURE:** Flask read-only UI on **loopback only**; token auth for telemetry APIs; no job dispatch / no shell routes.

**FILES:**

| Path | Role |
|------|------|
| `services/dashboard/auth.py` | Local token auth |
| `services/dashboard/telemetry.py` | Read-only sim/graph snapshots |
| `services/dashboard/app.py` | Flask factory + deny control routes |
| `services/dashboard/templates/dashboard.html` | UI + SVG graph |
| `services/dashboard/cli.py` | `nexo-dashboard` |
| `tests/test_s12_dashboard.py` | Auth + injection rejects |

**RISKS:** Exposing control APIs unbound (mitigated: loopback bind refuse, 401 without token, `/api/jobs|dispatch|execute|shell` → 405/403).

**TESTS:** Token required; graph/overview read-only; job injection rejected; CLI refuses `0.0.0.0`.

**ACCEPTANCE CRITERIA:**

- [x] Visualize nodes/beings/edges from sim  
- [x] Auth-local  
- [x] No job injection via UI  
- [x] Core untouched  

---

## S13 — Windows EXE

**OBJECTIVE:** `NEXO-Node.exe` packaging for Win10/11 x64 with consent-first install UX.

**ARCHITECTURE:** PyInstaller build scripts + Python policy modules. Manual signing/update channel. **No silent install. No Windows Service. Kill switch = `stop`.**

**FILES:**

| Path | Role |
|------|------|
| `services/packaging/windows/consent.py` | Explicit consent gate |
| `services/packaging/windows/silent_policy.py` | Reject `/S` `/quiet` … |
| `services/packaging/windows/layout.py` | User-local layout + uninstall plan |
| `services/packaging/windows/pipeline.py` | Signed build / manual update spec |
| `services/packaging/windows/cli.py` | `nexo-winpack` |
| `packaging/windows/*` | `build_exe.ps1`, `uninstall.ps1`, spec, entry |
| `tests/test_s13_windows_packaging.py` | Consent / silent / clean uninstall |

**RISKS:** AV false positives; silent install flags (mitigated: reject silent flags; no service registration).

**TESTS:** Consent required; silent flags rejected; uninstall leaves no services; pipeline manual.

**ACCEPTANCE CRITERIA:**

- [x] Explicit consent screens / statements  
- [x] Clean uninstall plan (no leftover services)  
- [x] Kill switch documented (`stop`)  
- [x] Core untouched  

---

## S14 — Debian DEB

**OBJECTIVE:** `nexo-node.deb` for Debian/Ubuntu x64 (ARM64 later) with user-level defaults.

**ARCHITECTURE:** Packaging metadata + optional `systemd --user` unit. Maintainer scripts **must not** enable system services, linger, or rc.d. Kill switch / disable remain owner-controlled.

**FILES:**

| Path | Role |
|------|------|
| `services/packaging/debian/policy.py` | No forced root persistence |
| `services/packaging/debian/layout.py` | User XDG layout + stop/disable |
| `services/packaging/debian/unit.py` | Optional user unit text |
| `services/packaging/debian/control.py` | `debian/control` generator |
| `services/packaging/debian/cli.py` | `nexo-debpack` |
| `packaging/debian/*` | control, postinst/prerm/postrm, unit, build script |
| `tests/test_s14_debian_packaging.py` | Policy + script safety |

**RISKS:** Root install by default (mitigated: policy + script checker; unit disabled by default).

**TESTS:** Policy flags; maintainer scripts reject `systemctl enable` (system) / linger; stop/disable commands documented.

**ACCEPTANCE CRITERIA:**

- [x] User-level stop/disable works (commands + unit ExecStop)  
- [x] No forced root persistence  
- [x] Core untouched  

---

## S15 — Real Multi-device Lab

**OBJECTIVE:** ≥2 voluntary devices, TLS policy, allowlisted jobs, reproducible experiment IDs, verified kill switches.

**ARCHITECTURE:** `services/lab/` rehearsal (in-process ≥2 nodes + coordinator + TextWorld) plus runbooks for physical TLS labs. FL disabled. No remote shell.

**FILES:**

| Path | Role |
|------|------|
| `services/lab/experiment_id.py` | Deterministic experiment IDs |
| `services/lab/tls_policy.py` | TLS 1.2+ / no plaintext / no FL |
| `services/lab/killswitch.py` | Owner stop verification |
| `services/lab/faults.py` | Signature / timeout / revoke / forbid battery |
| `services/lab/session.py` | MultiDeviceLabSession.rehearse |
| `services/lab/cli.py` | `nexo-lab` |
| `docs/experiments/S15_*.md` | Runbook, faults, checklist |
| `tests/test_s15_multi_device_lab.py` | Acceptance tests |

**RISKS:** Premature FL; security regressions (mitigated: FL flag forbidden; fault battery; fortress).

**TESTS:** Reproducible IDs; kill switch; rehearsal ≥2 devices; TLS policy; runbooks present.

**ACCEPTANCE CRITERIA:**

- [x] Reproducible experiment IDs  
- [x] Owner kill switches verified  
- [x] Fault injection expectations encoded  
- [x] Core fortress still green  

---

## S16 — Collective Learning

**OBJECTIVE:** Phase A/B distillation from shared experience claims — sandbox only; **no auto weight deploy**.

**ARCHITECTURE:** Distill A/B → eval gates → **manual** promote → rollback to prior promoted artifact. Explicit experimental disclaimer. FL is out of scope (S17).

**FILES:**

| Path | Role |
|------|------|
| `services/learning/models.py` | LearningArtifact / phases / statuses |
| `services/learning/sandbox.py` | Toy distill from claims |
| `services/learning/eval_gates.py` | Coverage / runaway / baseline gates |
| `services/learning/registry.py` | Active pointer + history |
| `services/learning/service.py` | Facade (run_ab / promote / rollback) |
| `services/learning/cli.py` | `nexo-learn` |
| `tests/test_s16_collective_learning.py` | Manual-only + rollback |

**RISKS:** Claiming proven cognition; silent rollout (mitigated: disclaimer; `auto_deploy=False`; `allow_auto` promote forbidden).

**TESTS:** A/B distill; eval rejects empty; promote manual; rollback restores prior; no federated imports.

**ACCEPTANCE CRITERIA:**

- [x] Manual promote only  
- [x] Rollback restores prior artifact  
- [x] Eval gates enforced  
- [x] Core untouched  

---

## S17 — Federated Learning Research

**OBJECTIVE:** Optional FL / LoRA-delta aggregation under an explicit research sandbox.

**ARCHITECTURE:** Opt-in `FederatedResearchFlag` (off by default) → validate client updates → FedAvg + LoRA merge → eval harness → paper-ready reproducibility bundle. **Never auto-deploys to Core.**

**FILES:**

| Path | Role |
|------|------|
| `services/learning/federated/flags.py` | Research opt-in |
| `services/learning/federated/updates.py` | Poison / integrity rejects |
| `services/learning/federated/aggregate.py` | FedAvg + LoRA delta |
| `services/learning/federated/evaluate.py` | Eval harness |
| `services/learning/federated/bundle.py` | Reproducibility bundle |
| `services/learning/federated/service.py` | Session facade |
| `services/learning/federated/cli.py` | `nexo-fl` |
| `tests/test_s17_federated_learning.py` | Opt-in + poison + bundle |

**RISKS:** Model poisoning; legal/privacy (mitigated: risk acknowledgement; NaN/norm/null-sig rejects; research-only purpose).

**TESTS:** Default off; malicious updates rejected; bundle hash + `core_unchanged`.

**ACCEPTANCE CRITERIA:**

- [x] Research flag required  
- [x] Paper-ready reproducibility bundle  
- [x] Core unchanged / no auto-deploy  
- [x] Malicious update rejected  

---

## Open-source identity

Root docs for contributors and reviewers:

- [`README.md`](README.md) — lab framing + Core demo
- [`ARCHITECTURE.md`](ARCHITECTURE.md)
- [`ROADMAP.md`](ROADMAP.md)
- [`SECURITY.md`](SECURITY.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- [`docs/experiments/`](docs/experiments/)

README framing:

> NEXO is an experimental distributed cognitive-agent laboratory.

Avoid asserting “artificial consciousness.”

---

## Immediate next commit recommendation

1. ~~S0–S17~~ done — Collective Swarm phase roadmap complete.  
2. ~~Open-source identity packaging~~ done.  
3. Keep SaaS residue out of the tree (`.gitignore` blocks `nexo_qa/product/`, `data/product.db`, portal prompts); run fortress before physical TLS labs.
