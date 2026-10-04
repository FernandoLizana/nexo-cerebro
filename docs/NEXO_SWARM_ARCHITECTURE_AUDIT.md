# NEXO Swarm — Architecture Audit

**Date:** 2026-09-06  
**Branch:** `nexo-collective-swarm`  
**Baseline commit:** `c5892c3e` — *Add NEXO Cognitive QA P1-P9…*  
**Package markers:** `nexo_qa.__phase__ = "P9"` · `__version__ = "0.9.0-p9"`  
**Mode:** AUDIT ONLY — Core cognitive logic was **not** rewritten in this delivery.

---

## Principle

> **NINGUNA FUNCIÓN DEL SWARM PUEDE COMPROMETER LA ESTABILIDAD DEL CORE.**

NEXO is no longer a commercial SaaS. It becomes an open-source **distributed cognitive-agent laboratory**. This audit freezes what must be protected before any multi-node work.

---

## 0. Snapshot

| Item | Value |
|------|--------|
| SaaS path | **Abandoned** (`feature/nexo-integrated-brain-v1` remains historical) |
| Lab plan | `docs/planes/NEXO_COGNITIVE_LAB_PLAN.md` (prior planning artifact) |
| `services/` | **Absent** — coordinator/node runtime are greenfield |
| P1 ActionSchema triad | Tracked under `nexo/core/` (completed in S1) |
| Residual SaaS | **REMOVED** from working tree; blocked in `.gitignore` (`nexo_qa/product/`, `data/product.db`, portal prompts) |
| Known Core debt | PFC still RoomWorld-locked (`ROOM_ACTION_SCHEMAS`); no `action_schemas=` kwarg |

---

## 1. Classification legend

| Class | Meaning |
|-------|---------|
| **KEEP** | Required for Swarm science; protect with fortress tests |
| **REFACTOR** | Keep substance; rename claims, slim API, or isolate |
| **ARCHIVE** | Keep off the Swarm hot path; comparator / history |
| **REMOVE** | SaaS, malware-adjacent, or noise that must not ship on nodes |
| **UNKNOWN** | Missing or insufficient evidence — design before reuse |

---

## 2. Top-level packages

| Package / entry | Class | Rationale |
|-----------------|-------|-----------|
| `nexo/` | **KEEP** + selective **REFACTOR** | Scientific `IntegratedRuntime`, scheduler, PFC/BG, WM/hippo |
| `nexo_qa/` | **KEEP** (+ **REMOVE** product) | P0–P9 harness: worlds, personas, metrics, population, chaos, human_lab |
| `brain/` | **ARCHIVE** / quarry **REFACTOR** | Monolithic `InfantApeBrain`; dual-executive risk if used as Being default |
| `configs/nexo_qa/**` | **KEEP** | Versioned experimental contracts |
| `configs/nexo/integrated_v90.yaml` | **KEEP** | Scientific freeze profile |
| `tests/test_p0`…`p9` | **KEEP** | Quality gates |
| `docs/cognitive_qa/` | **KEEP** | Scientific canon / ADRs |
| `app.py` | **REFACTOR** | Local lab UI — not a Swarm coordinator |
| `services/` | **UNKNOWN** (missing) | Must be designed greenfield |
| `nexo/demo/`, `nexo/behavioral/` | **ARCHIVE** | Demo/paper paths; keep off node runtime |
| `nexo_qa/product/` | **REMOVED** | Was untracked SaaS residue; now gitignored |
| `brain/web_fetch.py`, `web_search.py`, `youtube_tool.py` | **REMOVE** from Swarm jobs | Open egress; violates allowlist model |

---

## 3. `nexo_qa/` P0–P9

| Area | Paths | Class | Notes |
|------|-------|-------|-------|
| Package markers | `__init__.py` | **REFACTOR** | Later: mission → Collective Swarm / Lab; keep phase honest |
| MockWorld + bind | `testing/` | **KEEP** | Deterministic offline world |
| BrowserWorld + policy | `browser/` | **KEEP** | Controlled substrate; allowlist template for jobs |
| Perception / goals | `perception/`, `goals/` | **KEEP** | Engineering models, not validated human vision |
| Personas | `personas/` | **REFACTOR** | → Synthetic Cognitive Profiles / Being phenotypes |
| Analysis / metrics / failures | `analysis/`, `metrics/`, `failures/` | **KEEP** | Shared Experience backbone; metrics = experimental |
| Population / chaos | `population/`, `chaos/` | **KEEP** | Multi-agent experiment planning |
| Human lab | `human_lab/` | **REFACTOR** | Default `NO_HUMAN_DATA`; privacy helpers reusable |
| Product | `product/` | **REMOVE** | SaaS |

---

## 4. Critical Core (C1–C16)

| ID | Piece | Status @ tip | Paths | Protection rule |
|----|-------|--------------|-------|-----------------|
| **C1** | ActionSchema / EnvironmentProtocol | **OK (S1)** | `nexo/core/action_schema.py`, `environment_protocol.py`, `legacy_action_adapter.py` | Tracked modules; required for multi-world Beings |
| **C2** | SimulationClock | OK | `nexo/core/clock.py` | Discrete ticks only in trajectory identity |
| **C3** | StateStore | OK | `nexo/core/state_store.py` | Per-Being isolation for multi-Being processes |
| **C4** | RandomStreams | OK | `nexo/random_streams.py` | Never share RNGs across nodes |
| **C5** | CognitiveScheduler | OK | `nexo/core/scheduler.py` | In-process only; silent `except` is observability debt |
| **C6** | IntegratedRuntime + `trajectory_hash` | OK | `nexo/integrated_runtime.py` | Hash is freeze key; networking must not inject nondeterminism |
| **C7** | PFC | **OK (S1)** | `nexo/prefrontal/deliberation.py` | Accepts `action_schemas=`; Room catalog fallback; ignores metadata |
| **C8** | Basal ganglia | OK + Room leftovers | `nexo/basal_ganglia/` | `"rest"` fallback debt |
| **C9** | WM / hippocampus | OK | `nexo/working_memory/`, `nexo/memory/hippocampus/` | Local Intelligence memory |
| **C10** | MockWorld | OK | `nexo_qa/testing/mock_world.py` | Depends on C1 when imports are clean |
| **C11** | BrowserPolicy | OK | `nexo_qa/browser/policy.py` | Localhost allowlist; downloads/uploads off |
| **C12** | Persona mapping | OK | `nexo_qa/personas/mapping.py` | Being phenotype layer |
| **C13** | Population seeds / plan hash | OK | `nexo_qa/population/seeds.py`, `planner.py` | Reuse for signed experiment assignment |
| **C14** | Analysis → metrics | OK | `analysis/` → `metrics/` | Offline Shared Experience |
| **C15** | Failure taxonomy | OK | `failures/taxonomy.py` | Versioned agent-failure ontology |
| **C16** | MessageBus | OK **local-only** | `nexo/core/messages.py` | **Must never** become network I/O |

Historical v90 trajectory hash (documented):  
`77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c`

---

## 5. Coupling risks (R1–R14)

| ID | Risk | Naive Swarm failure mode |
|----|------|--------------------------|
| R1 | Dual executive `nexo` + `brain` | Non-reproducible “same Being” across nodes |
| R2 | RoomWorld verb lock-in | Remote catalogs invisible to PFC |
| R3 | Scheduler silent exceptions | Degraded Beings look healthy |
| R4 | MessageBus → sockets | Tick semantics + security collapse |
| R5 | Shared StateStore | Cross-Being contamination |
| R6 | Persistent `data/brain_state` | False “fresh seed” |
| R7 | Config mode sprawl | ExperimentSpec drift across nodes |
| R8 | Unbounded Playwright jobs | Resource exhaustion / egress |
| R9 | Local-FS population planner | Unsigned forgeable jobs |
| R10 | Hash excludes network jitter | False reproduction claims |
| R11 | Exposing `app.py` as control plane | Unauthenticated remote control |
| R12 | Connectome ≠ peer topology | Mixing tick edges with RTT |
| R13 | Raw trace upload | DOM / screenshot leakage |
| R14 | Dirty tree + SaaS residue | Divergent nodes / accidental product surface |

---

## 6. Security risks (S1–S12)

| ID | Risk | Constraint violated if ignored |
|----|------|--------------------------------|
| S1 | `brain/web_fetch` open URL | Allowlisted jobs / no scanning |
| S2 | Search/YouTube scrapers | Unallowlisted egress |
| S3 | Soft browser allowlist heuristics | External navigation |
| S4 | Automated Playwright install | Silent install risk |
| S5 | Missing `.[browser]` extra vs CI | Broken/overreaching install scripts |
| S6 | Flask lab as Swarm port | No TLS/auth control plane |
| S7 | MessageBus network temptation | Separate channel required |
| S8 | No node PKI yet | Keys must never leave device |
| S9 | Screenshots / HTML debug | Privacy minimization |
| S10 | Human-lab without redaction | PII |
| S11 | No job allowlist protocol | Arbitrary code execution risk |
| S12 | Residual `product/` | Not a voluntary scientific node |

**Hard prohibitions (design invariant):** network scanning, self-replication, silent installation, remote shell, arbitrary command execution, hidden persistence, credential harvesting, filesystem crawling, browser-history collection, keylogging, disabling antivirus, privilege escalation.

---

## 7. Test hygiene findings (addressed in S0/S1 fortress pass)

| Issue | Status in this delivery |
|-------|-------------------------|
| `tests/nexo_qa` shadowed package `nexo_qa` | Smoke files removed; `tests/conftest.py` prefers project package |
| `browser` marker missing under `--strict-markers` | Registered in `pyproject.toml` |
| PFC `action_schemas=` mismatch | **Documented debt** — Core not patched yet; fortress locks current signature |
| P1 triad untracked | **Documented** — commit-complete is S1 acceptance work |
| SaaS leftovers untracked | **REMOVE** in cleanup; do not commit |

---

## 8. Reuse map → Swarm layers

| Swarm layer | Reuse | Do not reuse as-is |
|-------------|-------|--------------------|
| Local Intelligence | `IntegratedRuntime`, PFC/BG, WM/hippo, `RandomStreams`, personas, Mock/Browser worlds | Full `InfantApeBrain` loop; demo bridges |
| Shared Experience | Trace capture, failure certificates, reporting, population aggregators | Raw screenshots/HTML; SaaS reports |
| Global Memory | Local hippo/SQLite patterns with Being namespaces | Auto-sync of `data/brain_state` without consent |
| Knowledge Graph | Connectome as **intra-agent** only; failure taxonomy as typed edges | Connectome as peer network |
| Federated Learning | Local TD learner only (future optional) | No FL protocol exists |

---

## 9. Golden baseline (this delivery)

| Scope | Result |
|-------|--------|
| Cognitive QA P0–P9 + fortress (`-m "not browser"`) | **157 passed / 0 failed** (S1) |
| Failures | none |
| Browser-marked | 85 deselected |

Artifacts:

- `artifacts/swarm/GOLDEN_BASELINE.json`
- `artifacts/swarm/cognitive_qa_regression_stdout.txt`
- `artifacts/swarm/cognitive_qa_junit.xml`
- `tests/test_swarm_core_fortress.py`

---

## 10. Immediate priorities (S0 → S1)

1. ~~Finish P1 contract (C1 + C7)~~ **done in S1**.  
2. Expand fortress coverage around trajectory hash + security deny-list.  
3. Quarantine SaaS residue from any node image.  
4. Design `services/` greenfield (TLS, keys, allowlisted jobs) — **implement later** (S2+).

**Next documents:** `docs/NEXO_SWARM_ARCHITECTURE.md`, `docs/NEXO_SWARM_SECURITY_MODEL.md`, `docs/planes/NEXO_SWARM_MASTER_PLAN.md`.
