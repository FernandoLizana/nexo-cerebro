# P6 — NCFS

**NEXO Cognitive Friction Score** — version `ncfs_v1`, range 0–100.

Components: perceptual, attention, semantic, memory, decision, navigation, recovery.

Coverage = available_components / 7 — missing data does not silently become zero friction.

Disclaimer: simulation-derived; not human-calibrated.

See `nexo_qa/metrics/ncfs.py` and `configs/nexo_qa/metrics/v1.yaml`.
