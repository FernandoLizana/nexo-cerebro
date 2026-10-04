# P1 — Regression report

## STRICT (must match P0 golden)

| Metric | P0 | P1 | Match |
|--------|----|----|-------|
| `trajectory_hash` | `77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c` | same | yes |
| `actions_taken` | 12× `explore` | 12× `explore` | yes |
| `final_energy` | `0.3526710863756767` | same | yes |
| ticks | 12 | 12 | yes |
| no crash | true | true | yes |

Config: `configs/nexo/integrated_v90.yaml`, seed 42, `NEXO_SKIP_GPU_BENCH=1`.

## STATISTICAL

| Metric | P0 | P1 |
|--------|----|----|
| `mean_reward` | 0.12 | 0.12 |
| `valid_certificates` | 12 | 12 |
| `agency_score` | 1.0 | 1.0 |
| `eat_ratio` | 0.0 | 0.0 |

## INFORMATIONAL

| Metric | P0 | P1 |
|--------|----|----|
| event_count | 421 | 421 |
| wall time (startup+12 ticks) | 3.44–3.69 s | 2.91–3.04 s |

`reward.received` and `action.selected` payloads gained optional keys. Hash ignores them.

## Tests

P0 freeze: 604 passed / 1 failed (`test_grounding` fridge distance) / 0 skipped.

P1 targeted smoke (80 tests): **80 passed** in 160 s — integrated core, reproducibility, body, sprints 71–78, executive, P1 new tests.

Full `pytest tests`: **631 passed / 0 failed / 0 skipped** in 3897.61 s (`artifacts/p1/full_junit.xml`).

The P0 known grounding failure **did not reproduce** in this full run. It is not treated as an intentional P1 behavioral fix; see `artifacts/p1/test_results.json`.

New tests (not skips of old ones):

- `tests/test_p1_action_schema.py`
- `tests/test_p1_environment_contract.py`
- `tests/test_p1_two_worlds_one_brain.py`
- `tests/test_p0_nexo_qa_import.py` (moved from `tests/nexo_qa/` to stop shadowing the `nexo_qa` package)

## Behavioral logic in PFC

Scoring formulas kept; **source** of candidates changed from a frozen Room list to `ActionSchema` affordances. `test_pfc_veto_inhibits_distractor_when_low_energy` still passes (eat vs inspect_distractor, energy 0.25).
