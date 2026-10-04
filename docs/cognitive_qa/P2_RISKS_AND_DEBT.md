# P2 — Risks and debt

## P2-RISK-001 · GOAL · MEDIUM · DEFERRED

Natural-language GOAL not consumed by PFC. Web Lab Pro completion not guaranteed. **P4**.

## P2-RISK-002 · PERCEPTION · MEDIUM · DEFERRED

DOM_FAST over-exposes structure vs human vision. **P3**.

## P2-RISK-003 · COGNITION · LOW

NEXO may loop on low-reward actions (e.g. repeated `focus`) on forms. Environment correctly executes; learning/goal stack not P2 scope.

## P2-RISK-004 · LEGACY · HIGH · UNCHANGED

`WorldDemoFacade` still lacks `available_actions` (P1-RISK-001).

## P2-RISK-005 · CI · LOW

Browser tests optional in CI (`continue-on-error`).

## P2-RISK-006 · SECURITY · MEDIUM

Allowlist is prefix-based; document before production browser QA.
