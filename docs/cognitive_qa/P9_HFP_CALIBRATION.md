# P9 — HFP Calibration

EHFP (P6) remains a **non-probability proxy** until validated.

HFP (Human Failure Probability) only when:

- human_data_status ≥ CALIBRATION
- holdout evaluated
- calibration_status VALIDATED
- domain scope CALIBRATED

`hfp_claim_allowed()` blocks claims otherwise.

Metrics: Brier score, ECE, calibration curve via `calibrate_ehfp_to_hfp()`.
