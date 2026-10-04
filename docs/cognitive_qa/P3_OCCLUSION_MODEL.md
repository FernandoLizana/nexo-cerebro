# P3 — Occlusion model

Approximate occlusion via fixed JS: `document.elementFromPoint(centerX, centerY)`.

If top element is not the target (and neither contains the other), `occlusion_score = 0.85` → relation `OCCLUDED`.

**Limitations:** no full renderer; stacked partial transparency not modeled; center-point only.

Sufficient for modal overlay scenarios in Web Lab P3.
