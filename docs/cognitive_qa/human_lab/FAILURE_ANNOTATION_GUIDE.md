# Failure Annotation Guide

Human reviewers annotate observed failures — P6 taxonomy is **not** automatic ground truth.

## Families
Use P6 families (ATTENTION, MEMORY, NAVIGATION, GOAL, …) when evidence supports.

## Rules
- Require observable evidence (action sequence, error message, abandonment)
- Use `UNCLASSIFIED` when ambiguous
- Do not infer internal cognitive state without behavioral evidence
- Machine label ≠ adjudicated label until reviewer confirms

## Causal wording
Prefer: associated_with, preceded, contributed_to — not caused_by unless strong evidence.
