# P2 — Overview

P2 adds **BrowserWorld** — the first real web environment for NEXO Cognitive QA.

```text
Cognitive Core → EnvironmentProtocol → ActionSchema[]
        Legacy / Mock / BrowserWorld
                              │
                    BrowserDriverProtocol
                              │
                         Playwright → Chromium → Web Lab (local)
```

## Delivered

- `nexo_qa/browser/` — models, policy, PlaywrightDriver, action_mapper, BrowserWorld
- `tests/fixtures/web_lab/` — offline 5-page lab
- `configs/nexo_qa/browser_lab.yaml`
- 11 browser tests + `test_three_worlds_one_brain`
- Optional dependency `playwright` via `.[browser]`

## Not delivered (by design)

Vision models, OCR, personas, friction scores, LLM planner, SaaS, internet crawling.

## Quality gate

`artifacts/p2/quality_gate.json` — **PASS**

## Limitation

`P2_LIMITATION_GOAL_SEMANTICS`: GOAL string is documentation/oracle context; PFC does not parse natural language yet. NEXO may not complete Pro plan without P4 goal wiring.
