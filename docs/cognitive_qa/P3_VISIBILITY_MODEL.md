# P3 — Visibility model

`visibility_score` (0–1) is **structural visibility**, not human probability.

Computed from viewport intersection fraction of bounding box. Relations: `FULLY_VISIBLE`, `PARTIALLY_VISIBLE`, `OFFSCREEN_*`, `OCCLUDED`.

Offscreen elements are excluded from HYBRID percepts. Occlusion uses `elementFromPoint` center sample (see `P3_OCCLUSION_MODEL.md`).
