# P3 — Risks and debt

| Risk | Mitigation |
|------|------------|
| Occlusion false negatives/positives | Documented; oracle tests only |
| Salience not human-calibrated | Explicit ENGINEERING DEFAULT label |
| VISION stub confusion | Raises NotImplementedError |
| DOM_FAST vs HYBRID drift | Default dom_fast; explicit config for hybrid |
| Attention gate vs NEXO attention duplication | Gate is pre-cortical filter only |

## Debt

- Screenshot keyframes not fully wired to artifact store
- No mobile viewport matrix
- Password field redaction basic (pattern-based)
- PERCEPTUAL_MISS event prepared but not KPI-ready
