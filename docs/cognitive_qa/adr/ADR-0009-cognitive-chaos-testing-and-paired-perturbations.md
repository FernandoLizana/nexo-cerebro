# ADR-0009 — Cognitive Chaos Testing and Paired Perturbations

## Status

Accepted — P8

## Context

P7 runs populations with BASELINE conditions. P8 must inject controlled environmental degradations and measure cognitive impact via paired comparison without mutating persona/cognitive state directly.

## Decision

1. Add `nexo_qa/chaos/` with versioned `PerturbationSpec`, `PerturbationController`, and `ChaoticMockWorld`.
2. Paired design: same task/persona/seed; only condition/perturbation differs (`derive_paired_seed`).
3. Environment boundary — perturbations modify world/perception/outcomes only.
4. P6/P7 remain metric source of truth; P8 adds `PairedChaosDelta` and chaos reports.
5. Lazy-load `BrowserWorld` in `nexo_qa.browser` to fix import cycle for mock-world chaos runs.

## Consequences

- P9 can calibrate against paired baseline/perturbed datasets.
- Web Lab chaos HTML fixtures ready for browser backend wiring.
- Invalid pairs reported with transparent denominators.
