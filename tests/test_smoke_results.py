"""Tests resultados smoke + schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SMOKE_DIR = ROOT / "results" / "smoke"
SCHEMA_PATH = ROOT / "schemas" / "experiment_result.schema.json"

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module", autouse=True)
def _ensure_smoke():
    import subprocess
    import sys

    subprocess.run([sys.executable, "-m", "experiments.run_smoke_experiments"], cwd=ROOT, check=True)


def _load_smoke(name: str) -> dict:
    p = SMOKE_DIR / name
    assert p.is_file(), f"missing {p}"
    return json.loads(p.read_text(encoding="utf-8"))


def test_smoke_results_exist():
    files = list(SMOKE_DIR.glob("*.json"))
    assert len(files) >= 5


def test_smoke_results_record_all_flags():
    data = _load_smoke("baseline_legacy_seed_42.json")
    assert isinstance(data["flags"], dict)
    assert len(data["flags"]) > 10


def test_smoke_results_record_config_hash():
    data = _load_smoke("roadmap100_full_v1_seed_42.json")
    assert len(data["config_hash"]) == 64


def test_same_seed_smoke_result_is_reproducible():
    import subprocess
    import sys

    subprocess.run([sys.executable, "-m", "experiments.run_smoke_experiments"], cwd=ROOT, check=True)
    a = _load_smoke("baseline_legacy_seed_42.json")["trajectory_hash"]
    subprocess.run([sys.executable, "-m", "experiments.run_smoke_experiments"], cwd=ROOT, check=True)
    b = _load_smoke("baseline_legacy_seed_42.json")["trajectory_hash"]
    assert a == b


def test_different_seed_smoke_changes_trajectory():
    a = _load_smoke("roadmap100_full_v1_seed_42.json")["trajectory_hash"]
    b = _load_smoke("roadmap100_full_v1_seed_99.json")["trajectory_hash"]
    assert a != b


def test_smoke_results_validate_required_fields():
    data = _load_smoke("roadmap100_no_binding_v1_seed_42.json")
    for key in ("schema_version", "experiment", "condition", "seed", "config_hash", "flags", "metrics"):
        assert key in data
