# P3 — Perceptual diff

`diff_scenes(previous, current)` in `nexo_qa/perception/diff.py`.

Detects: `appeared`, `disappeared`, `moved`, `text_changed`, `state_changed`, `salience_changed`, `focus_changed`.

Keyed by `source_element_id` for continuity across scenes. Emitted in `BrowserWorld` trace as `PERCEPTUAL_DIFF`.

Used by error-message scenario: alert appears after invalid submit.
