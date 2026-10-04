# P2 — DOM_FAST perception

**DOM_FAST ≠ human vision.** Engineering approximation for P2 integration only.

## Input

Playwright page + in-page JS (`playwright_driver._DOM_FAST_SCRIPT`):

- Visible `button`, `a`, `input`, `textarea`, `select`, headings
- Filters: `display:none`, `visibility:hidden`, `aria-hidden`, zero-size boxes, `input[type=hidden]`

## Output to cognition

Generic P1 percept tuples: `(modality, salience, (label_hash, visibility, region_hash))`.

Internal `BrowserElementSnapshot` (not passed to PFC): role, text, bbox, `web:e:NNNN`.

## Cheating mitigations

- `data-testid` used only in driver locator map
- No CSS classes/IDs in ActionSchema
- No full HTML dump (unless `debug_capture_html: true`)

## P3

HYBRID/VISION modes, salience, clutter, viewport attention.
