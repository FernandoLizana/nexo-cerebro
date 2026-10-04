# P3 — Handoff to P4

## Delivered

- Perceptual web model (`WebPercept`, `PerceptualScene`, `PerceptualDiff`)
- HYBRID perception with salience, occlusion, clutter, attention gate
- Web Lab P3 scenarios + oracle manifest
- 20 P3 tests, docs, ADR-0004

## Not in P3

- VISION mode implementation
- NL goal → PFC wiring
- OCR / VLM / GPU vision
- Population / persona variance
- Commercial perceptual-miss KPIs

## P4 suggestions

- Semantic grouping from accessible names and task context
- Stronger error/alert novelty → attention boost via existing NEXO novelty
- Multi-viewport smoke (mobile)
- Calibrated salience (P9 track)

## Config entry point

`configs/nexo_qa/p3_perception.yaml` — set `perception.mode: hybrid` on `BrowserConfig`.
