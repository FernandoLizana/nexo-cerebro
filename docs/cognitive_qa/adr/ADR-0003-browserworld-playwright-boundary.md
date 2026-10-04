# ADR-0003 — BrowserWorld and Playwright boundary

**Status:** Accepted · **Date:** 2026-08-19

## Context

P1 formalized `EnvironmentProtocol` and `ActionSchema`. P2 must add real web interaction without leaking Playwright/DOM into cognition.

## Decision

Three layers:

```text
Cognitive Core → EnvironmentProtocol → BrowserWorld → BrowserDriverProtocol → PlaywrightDriver → Chromium
```

- **BrowserWorld** implements P1 contract only.
- **PlaywrightDriver** is optional (`pip install -e ".[browser]"`).
- **DOM_FAST** perception: visible interactive elements → generic percept tuples + `ActionSchema[]`.
- Locators live in driver registry keyed by `web:e:NNNN`, never in `ActionSchema.metadata` for cognition.

## Selector secrecy

Cognition sees labels like `activate "Comenzar"`. Driver may use `data-testid` internally.

## Security

Allowlist `127.0.0.1` / `localhost` only; `POLICY_BLOCKED` for external URLs; downloads/uploads disabled.

## Deferred

Vision/OCR/salience → P3. Natural-language goal parsing → P4+. Personas/friction → later.

## Consequences

Same core runs Legacy, Mock, Browser. v90 golden unchanged. Goal completion on Web Lab not guaranteed (honest autonomy).
