# P3 — Perceptual scene

`PerceptualScene` (`nexo_qa/perception/models.py`) is serializable and Playwright-independent.

## Fields

- `scene_id`, `url`, `viewport`, `scroll_position`
- `percepts`: tuple of `WebPercept`
- `regions`: optional `PerceptualRegion` groupings
- `focused_percept_id`, `attended_percept_ids`, `focal_percept_ids`, `peripheral_percept_ids`
- `global_context`, `timestamp`, `mode`, `exclusion_audit`

## WebPercept

Each percept represents what the agent *can* perceive — not internal DOM handles.

Includes: geometry (`bounding_box`, `bbox_norm`, `visual_region`), structural visibility, salience, clutter, occlusion, attention tier, and audit fields (`label_source`, `percept_sources`).

**Excluded from cognition:** selectors, XPath, `data-testid`, Playwright objects.

## Lifecycle

`source_element_id` is stable within a snapshot; `percept_id` may change across scenes. Same element can produce different percepts after scroll or DOM change.
