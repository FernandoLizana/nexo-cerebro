# P0 — Test baseline

Executed 2026-08-18 on Python 3.11.0 / Windows 10.0.26200.  
Command: `python -m pytest tests/ -q --junitxml=artifacts/baseline/p0/full_junit.xml`  
Env: `NEXO_SKIP_GPU_BENCH=1`

## Collection

| Moment | Count |
|--------|-------|
| `pytest --collect-only` at P0 start | **605** |
| After adding `tests/nexo_qa/test_p0_import.py` | **606** |

`norecursedirs` in `pyproject.toml` excludes `artifacts/`, `publication_finalization/`, `pack_gpt_adaptive_behavior/`, `publication_evidence/`, `dist/`, `data/`.

No import failures during collection. `pytest-asyncio` deprecation warning (unset loop scope) — preexisting, not a failure.

## Progression

| Layer | Command / scope | Result |
|-------|-----------------|--------|
| collect | `--collect-only` | 605 then 606 |
| smoke/core | `test_integrated_core`, `test_reproducibility`, `test_body_homeostasis`, sprints 71–78 | **46 passed** in 113 s |
| nexo_qa | `tests/nexo_qa/test_p0_import.py` | **1 passed** |
| full | `pytest tests/` | **604 passed, 1 failed**, 0 skipped, 0 errors, 1666 s |

CI subset (`.github/workflows/tests.yml`) was **not replaced**. P0 appended only the nexo_qa import smoke step.

## Full suite totals (JUnit)

| Metric | Value |
|--------|-------|
| tests_collected (executed freeze) | 605 |
| tests_passed | 604 |
| tests_failed | 1 |
| tests_skipped | 0 |
| tests_xfailed | 0 |
| tests_errors | 0 |

## PREEXISTING_FAILURE (not fixed)

**test:** `tests/test_grounding.py::test_grounding_can_guide_motivated_navigation_without_forcing_choice`

**error:** `assert after_distance < before_distance` → `345.48 < 344.72` is false (agent slightly farther from fridge after 12 ticks).

**probable cause:** grounding speech is a **bias**, not a motor command. Headless 12 ticks did not produce net approach. The test already asserts speech does not change `choice_key` immediately.

**reproducibility:** failed in this full P0 run. P0 did not edit `brain/grounding.py` or the test.

**severity:** MEDIUM (legacy demo navigation), not a v90 integrated scheduler crash.

**relation to Cognitive QA:** useful reminder of PRINCIPLE 5 (no success by force). Do not “fix” by teleporting the agent.

**recommendation:** document only. Separate commit if ever fixed.

## Classification

| Class | Examples |
|-------|----------|
| FAST | unit tests under `tests/test_td_reward.py`, `test_decision_audit.py`, nexo_qa import |
| NORMAL | most `test_*_integrated.py` sprints 1–50 |
| HEAVY | `test_smoke_results.py` (267 s + 141 s setup), several `test_sprints_55_58_*` (68–109 s), `test_sprints_51_54` timing (75 s) |
| GPU | `test_bench_e7.py` warns CUDA path missing; does not fail; `NEXO_SKIP_GPU_BENCH=1` |
| EXPERIMENTAL | `experiments/personal/*` — **not** in pytest |
| EXTERNAL | `test_web_search.py` collected; passed in this run (no network declared required) |

## Markers

`slow`, `integration` exist in `pyproject.toml`. Full suite did not skip via markers (`-ra --strict-markers`).
