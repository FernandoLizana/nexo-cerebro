# ADR-0004 — Hybrid perceptual web model (P3)

## Status

Accepted — P3 (2026-08-19)

## Context

P2 delivered `BrowserWorld` with flat DOM_FAST perception: all visible elements became percepts and actions. P3 must limit what NEXO receives using visibility, salience, occlusion, and attention — without exposing selectors or breaking P1/P2 contracts.

## Decision

1. Introduce `nexo_qa/perception/` with `WebPercept`, `PerceptualScene`, `PerceptualDiff`, and three modes: `dom_fast`, `hybrid`, `vision` (stub only).
2. `HybridPerception` combines DOM/accessibility with viewport geometry, contrast, occlusion (`elementFromPoint`), and heuristic salience.
3. `PerceptualAttentionGate` limits attended percepts before cognition; actions on elements require eligible percepts (global scroll/back exempt).
4. Extend `BrowserSnapshot` with `scroll_position` and `element_meta`; do not duplicate Playwright types in cognition.
5. Default remains `dom_fast` for P2 compatibility; `hybrid` is opt-in via `configs/nexo_qa/p3_perception.yaml`.

## Consequences

- NEXO receives a bounded perceptual scene, not the full DOM.
- P2 tests pass unchanged (`mode=dom_fast`).
- v90 golden hash unchanged (12 ticks, seed 42).
- VISION mode raises `NotImplementedError` — no false capability claims.

## Alternatives rejected

- Full computer vision stack (YOLO/VLM) — out of P3 scope.
- Replacing NEXO attention with a parallel WebAttentionEngine — rejected; gate feeds existing thalamic/perceptual pipeline via `percepts_for_agent()`.
