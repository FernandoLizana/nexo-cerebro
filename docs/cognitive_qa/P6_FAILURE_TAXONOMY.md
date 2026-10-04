# P6 — Failure Taxonomy

Version: **failures-v1**

| Family | Example types |
|--------|---------------|
| PERCEPTION | PERCEPTUAL_MISS, TARGET_OFFSCREEN |
| ATTENTION | DISTRACTOR_CAPTURE, TARGET_VISIBLE_NOT_ATTENDED |
| MEMORY | WORKING_MEMORY_LOSS |
| NAVIGATION | NAVIGATION_LOOP, STAGNATION |
| PROGRESS | GOAL_DRIFT, NO_PROGRESS |
| POLICY | ACTION_POLICY_BLOCKED |
| UNKNOWN | UNCLASSIFIED_FAILURE |

Full table: `artifacts/p6/failure_taxonomy.json`

Classifier: `nexo_qa/failures/classifier.py` — rule-based, no golden path.
