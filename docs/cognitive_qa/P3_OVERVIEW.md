# P3 — Overview (NEXO Cognitive QA)

## Mission

Replace flat DOM perception with a **limited, auditable perceptual web model**. NEXO receives a `PerceptualScene`, not the full page.

## Architecture

```text
WEB (Web Lab)
  ↓
BrowserSnapshot (+ hybrid metadata)
  ↓
PerceptionStrategy (dom_fast | hybrid | vision-stub)
  ↓
PerceptualScene
  ↓
PerceptualAttentionGate
  ↓
Action mapping (eligible percepts only)
  ↓
NEXO Cognitive Core
```

## Modes

| Mode | Status | Use |
|------|--------|-----|
| `dom_fast` | Complete | P2 baseline, regression |
| `hybrid` | Complete | P3 primary — geometry, salience, occlusion |
| `vision` | NOT_IMPLEMENTED | Contract only |

## Key invariants

- **Selector secrecy** — no CSS/XPath/locators in cognitive output.
- **Action requires perception** — element actions link to `source_percept_id`.
- **Visibility ≠ attention** — documented separately.
- **Salience = heuristic proxy** — ENGINEERING DEFAULT, NOT HUMAN-CALIBRATED.

## Verdict

**PASS** — 20 P3 tests, P2/P1 regression green, v90 golden intact.
