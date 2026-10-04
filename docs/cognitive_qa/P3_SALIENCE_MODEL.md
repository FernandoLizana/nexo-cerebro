# P3 — Salience model

`salience_score` is a **heuristic proxy** — ENGINEERING DEFAULT, NOT HUMAN-CALIBRATED.

Inputs: normalized area, centrality, contrast ratio, role prior, focus boost, modal boost. Weights configurable in `SalienceWeights`.

Does not encode page-specific rules (no `if text == "Pro"` hacks).
