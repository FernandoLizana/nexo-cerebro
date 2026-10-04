# P8 — Interruption Model

`INTERRUPTION` adds visible overlay percept, blocks non-allowed actions for `duration_ticks`.

Goal preserved in NEXO — site may interrupt, cognition not cleared.

Recovery: `interruption_recovery_ticks` in run summary when progress resumes.

Implementation: `PerturbationController` + `ChaoticMockWorld`
