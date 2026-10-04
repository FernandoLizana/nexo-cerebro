# ADR-0007 — Cognitive QA Metrics and Failure Certificates

**Status:** Accepted · **Phase:** P6

## Decision

1. **Raw evidence first** — metrics derive from normalized events, not invented explanations.
2. **QA layer in `nexo_qa/`** — NCFS/EHFP/CRS do not contaminate scientific core.
3. **Failure taxonomy** `failures-v1` with `UNCLASSIFIED_FAILURE` fallback.
4. **Rule-based offline classifier** — no golden path, no LLM required.
5. **Cognitive Failure Certificate** — extends causal certificate pattern; selector secrecy enforced.
6. **EHFP is NOT a probability** until P9 calibration.
7. **Offline reanalysis** — raw trace JSON immutable; derived reports versioned.

## Implications

- **P7:** population engine consumes run summaries + certificates.
- **P9:** EHFP features → calibration model.
