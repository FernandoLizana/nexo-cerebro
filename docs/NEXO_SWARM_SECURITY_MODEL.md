# NEXO Collective Swarm — Security Model

**Status:** DESIGN BASELINE  
**Audience:** node owners, contributors, reviewers  
**Non-goal:** product multi-tenant SaaS security (abandoned)

---

## 1. Threat posture

NEXO nodes are **voluntarily installed** by their owners for scientific participation.

We assume:

- some nodes may be malicious or compromised;
- some Beings may emit spam, poisoned “memories”, or contradictory claims;
- the coordinator is a high-value target;
- curious owners will inspect traffic and storage.

We do **not** assume:

- a right to scan LANs;
- a right to persist against uninstall;
- a right to execute arbitrary remote code;
- that “collective intelligence” justifies silent privilege escalation.

---

## 2. Hard prohibitions

The following are **forbidden** in NEXO Node, Coordinator, jobs, and Beings:

| Forbidden | Rationale |
|-----------|-----------|
| Network scanning / host discovery | Not science; abusive |
| Self-replication / worm-like propagation | Malware |
| Silent / hidden installation | Consent |
| Remote shell / arbitrary command execution | RCE |
| Hidden persistence / anti-uninstall tricks | Consent |
| Credential harvesting / keylogging | Privacy crime |
| Filesystem crawling / browser-history collection | Data minimization |
| Disabling antivirus / privilege escalation | Hostile |

**Only** declared, allowlisted NEXO jobs may run.

---

## 3. Consent & ownership

1. Owner installs the node explicitly.  
2. Owner configures resource limits and schedules.  
3. Owner can **STOP NEXO NODE** at any time (kill switch).  
4. Owner can uninstall without fighting persistence.  
5. Private keys stay on device; public keys register with the coordinator.  
6. Manual updates by default; any automatic update must be signed, versioned, and opt-in.

---

## 4. Cryptography & transport

| Requirement | Rule |
|-------------|------|
| Transport | TLS for node ↔ coordinator |
| Identity | Asymmetric keypair per node |
| Private key | Never leaves device; never logged |
| Messages | Signed; reject bad signatures |
| Updates | Signed artifacts only |
| Revocation | Coordinator can revoke node trust; node can wipe local trust store |

---

## 5. Job allowlist

Jobs are **typed protocols**, not shell strings.

Examples allowed later:

- `RUN_TEXTWORLD_EXPERIMENT`
- `RUN_BEING_INTERACTION`
- `RUN_BROWSERWORLD_EXPERIMENT`

Rejected by design:

- `EXECUTE_SHELL`
- `INSTALL_PACKAGE`
- `OPEN_URL` outside BrowserPolicy
- `READ_PATH` outside Being/experiment sandboxes

Unknown job types → **reject** (fail closed).

---

## 6. Sandbox & ResourceGovernor

| Control | Behavior |
|---------|----------|
| Isolation | containers / subprocess isolation per platform |
| Timeouts | every job has a hard deadline |
| CPU / RAM / GPU / disk / net | user-configured caps |
| Over-limit | `THROTTLE` → `PAUSE` → `TERMINATE JOB` |
| Hang | job must not block the node indefinitely |

BrowserWorld inherits P2 rules: localhost-oriented allowlist, downloads/uploads off, external navigation blocked by default.

---

## 7. MessageBus ≠ network

`nexo/core/messages.py` is an **in-process** tick queue for the scientific Core.

Swarm networking must use a **separate** channel with:

- explicit schemas;
- signature verification;
- rate limits;
- quarantine for untrusted payloads.

Wiring Core MessageBus to sockets is a **security regression**.

---

## 8. Experience poisoning defenses

Global memory pipeline:

```text
RAW → VALIDATION → QUARANTINE → DEDUPE
   → CROSS-NODE COMPARE → CONFIDENCE
   → CANDIDATE → PROMOTED
```

Defends against: spam, hallucinations, defective agents, adversarial memories.

No automatic promotion. No automatic model rollout.

---

## 9. Privacy & data minimization

| Data | Policy |
|------|--------|
| Private user chats | **Never** auto-upload |
| NEXO world interactions | May be research data **if** owner opted into the experiment |
| Hardware profile | Coarse capability fields only |
| Traces / screenshots | Redact PII; prefer summaries |
| Human-lab data | Existing privacy helpers; default `NO_HUMAN_DATA` |

---

## 10. Fault & abuse cases to test

Simulate and recover from:

- disconnect, packet loss, duplicate/delayed/corrupt events;
- bad signature, outdated protocol;
- worker crash, coordinator restart;
- over-quota jobs, revoked nodes.

---

## 11. Mapping to existing controls

| Existing | Swarm reuse |
|----------|-------------|
| `BrowserPolicy` | Template for origin allowlists |
| `docs/cognitive_qa/P2_SECURITY_MODEL.md` | Local web lab posture |
| `human_lab/privacy.py` | Redaction patterns |
| Fortress deny-list tests | Static guard for future `services/` |

| Must not ship on nodes | Why |
|------------------------|-----|
| `brain/web_fetch.py`, `web_search.py`, `youtube_tool.py` | Open egress |
| `nexo_qa/product/` | SaaS surface |
| Unauthenticated `app.py` exposure | Control-plane hole |

---

## 12. Security acceptance for early phases

**S0/S1 (now):** documentation + fortress tests + Core baseline; **no** network code.

**Before first real multi-device lab (S15) — toolkit + runbooks landed:**

- [x] TLS policy + signed messages (identity / heartbeats; physical TLS in runbook)  
- [x] Job allowlist enforced  
- [x] Kill switch verified  
- [x] ResourceGovernor verified (S2+)  
- [x] Quarantine pipeline stubbed (S7/S9)  
- [x] Security deny-list / fortress coverage for node packages  
- [x] Explicit owner consent UX (S13/S14)  

Physical multi-device execution still follows `docs/experiments/`; use **Swarm Simulator** / `nexo-lab rehearse` before opening real links.
