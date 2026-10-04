"""Pytest hygiene for NEXO Collective Swarm / Cognitive Lab.

Ensures repo-root ``nexo_qa`` wins over any path that would import
``tests/nexo_qa`` under the same top-level name. Does not alter Core behavior.

Also isolates brain persistence into a disposable directory so the suite never
writes into the user's live ``data/brain_state/``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROJECT_NEXO_QA = ROOT / "nexo_qa" / "__init__.py"
TESTS_DIR = ROOT / "tests"
USER_BRAIN_STATE = (ROOT / "data" / "brain_state").resolve()


def _prefer_project_nexo_qa() -> None:
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    elif sys.path[0] != root:
        sys.path.remove(root)
        sys.path.insert(0, root)

    # Pytest may insert tests/ ahead of ROOT; that shadows package ``nexo_qa``.
    tests = str(TESTS_DIR)
    while tests in sys.path:
        sys.path.remove(tests)

    existing = sys.modules.get("nexo_qa")
    if existing is None:
        return
    current = Path(getattr(existing, "__file__", "") or "")
    try:
        same = current.resolve() == PROJECT_NEXO_QA.resolve()
    except OSError:
        same = False
    if same:
        return
    for key in list(sys.modules):
        if key == "nexo_qa" or key.startswith("nexo_qa."):
            del sys.modules[key]


_prefer_project_nexo_qa()


@pytest.fixture(autouse=True)
def _isolate_cerebro_state_dir(tmp_path_factory: pytest.TempPathFactory):
    """Point ``CEREBRO_STATE_DIR`` at a fresh temp tree for every test.

    Protects the live user state under ``data/brain_state/`` even when a test
    constructs ``InfantApeBrain()`` without an explicit ``state_dir``.

    Scoped per test, not per session: a shared directory lets one test's
    persisted memories bleed into the next brain built in the same session,
    which breaks same-seed comparisons such as
    ``test_same_seed_reproduces_full_trajectory``.
    """
    isolated = tmp_path_factory.mktemp("cerebro_brain_state")
    previous = os.environ.get("CEREBRO_STATE_DIR")
    os.environ["CEREBRO_STATE_DIR"] = str(isolated)
    try:
        yield isolated
    finally:
        if previous is None:
            os.environ.pop("CEREBRO_STATE_DIR", None)
        else:
            os.environ["CEREBRO_STATE_DIR"] = previous


@pytest.fixture(scope="session", autouse=True)
def _isolate_cerebro_library_dir(tmp_path_factory: pytest.TempPathFactory):
    """Point ``CEREBRO_LIBRARY_DIR`` at an empty temp tree.

    Sleep-study ticks otherwise open the user's multi-MB PDFs under
    ``data/library/`` and hang the suite (see P1-4).
    """
    isolated = tmp_path_factory.mktemp("cerebro_library")
    previous = os.environ.get("CEREBRO_LIBRARY_DIR")
    os.environ["CEREBRO_LIBRARY_DIR"] = str(isolated)
    try:
        yield isolated
    finally:
        if previous is None:
            os.environ.pop("CEREBRO_LIBRARY_DIR", None)
        else:
            os.environ["CEREBRO_LIBRARY_DIR"] = previous
