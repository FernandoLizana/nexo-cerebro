# P3 — Hybrid perception

## Pipeline

1. `PlaywrightDriver.snapshot(mode="hybrid")` runs fixed internal JS (`_HYBRID_SCRIPT`).
2. Collects elements with bbox, visibility fraction, occlusion score, fg/bg colors, landmarks, modal flag.
3. `HybridPerception.build_scene()` computes salience, regions, clutter.
4. `PerceptualAttentionGate` ranks by `salience × visibility × (1 - occlusion)` and applies budget.

## Salience

Weighted sum of size, centrality, contrast, role prior, focus boost, modal boost. Weights in `PerceptionConfig.salience` — **ENGINEERING DEFAULT — NOT HUMAN-CALIBRATED**.

## Occlusion

Approximate via `document.elementFromPoint` at element center. Score ≥ 0.55 → `OCCLUDED`, excluded from actions.

## Screenshots

Config `screenshot_policy: keyframes` reserved for artifacts; P3 does not pass pixels to NEXO cognition.

## Config

See `configs/nexo_qa/p3_perception.yaml`.
