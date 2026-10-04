# P0 — Baseline freeze (NEXO integrated_v90)

This is the human-readable freeze record. Machine-readable copies live in `artifacts/baseline/p0/`.

## Identity

| Field | Value |
|-------|-------|
| Project | NEXO |
| Baseline | `integrated_v90` |
| Phase | P0 |
| Git commit | `3a0233c3c4fe504bcad5b545d7bbc43d0e6c2608` |
| Branch | `feature/nexo-integrated-brain-v1` |
| Python | 3.11.0 |
| Platform | Windows-10-10.0.26200-SP0 |
| `nexo.__version__` | 0.2.0 |
| Config | `configs/nexo/integrated_v90.yaml` |
| Tag | `integrated_v90` (preexisting) |

`COMMIT_HASH.txt` still says `NO_GIT_REPOSITORY` (stale). Git is the source of truth.

## What P0 changed in code

- Created `nexo_qa/` skeleton (no QA logic).
- Created `tests/nexo_qa/test_p0_import.py`.
- CI: extra step for that import test (existing subset **unchanged**).
- `pyproject.toml`: include `nexo_qa*`.
- `.gitignore`: keep `artifacts/` ignored except `artifacts/baseline/p0/` JSON/docs; add future secret/session patterns.

**No changes** to memory, deliberation, perception, PFC, reward, sleep, certificates, agency algorithms, or v90 YAML values.

## Quality gates (see completion report)

| Gate | Status |
|------|--------|
| A Repository | PASS — inventory + architecture map |
| B Testing | see `P0_TEST_BASELINE.md` |
| C Reproducibility | PASS — identical `trajectory_hash` A vs B |
| D Architecture | PASS — contract + coupling + hardcoded actions documented |
| E Scientific preservation | PASS — certificate/agency/event log documented, not modified |
| F Cognitive QA | PASS — namespace + principles + ADR + handoff; **no web** |

## Zero behavioral regression

Golden: seed 42, 12 ticks, hash `77b06e9fd77e5ca681663791fb0321e37fb63ff4d6407e68e92cf2275cce1d9c`, actions 12× `explore`.

P0 did not modify the cognitive loop, so before ≈ after by construction, confirmed by two consecutive runs.
