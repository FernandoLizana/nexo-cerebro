# ADR-0010 — Human Calibration and Domain-Scoped Validation

## Status

Accepted — P9 (CONDITIONAL PASS pending human data)

## Context

P8 provides paired perturbation datasets. P9 must enable evidence-based comparison with real humans without inventing validation or silently converting EHFP into human probability.

## Decision

1. Add `nexo_qa/human_lab/` with study specs, event normalization, datasets, alignment, HBC, and calibration engine.
2. `HumanDataStatus=NO_HUMAN_DATA` until real participants — verdict **CONDITIONAL PASS**.
3. HFP claims blocked unless holdout-validated within `CalibrationDomain`.
4. OOD policy returns HFP=NOT_AVAILABLE outside domain.
5. Synthetic fixtures test plumbing only — labeled NOT HUMAN VALIDATION.
6. ncfs_v1 / crs_v1 / ehfp_v1 preserved; recalibration requires new versions.

## Consequences

- P10 can expose calibration status in product UI.
- Real studies use pilot_study.yaml + ethics templates without code changes.
