"""Guard: tests must never resolve state into the user's live brain_state."""

from __future__ import annotations

from pathlib import Path

from brain.mind import InfantApeBrain, get_default_state_dir

ROOT = Path(__file__).resolve().parent.parent
USER_BRAIN_STATE = (ROOT / "data" / "brain_state").resolve()


def _is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def test_resolved_default_state_dir_is_not_user_brain_state():
    resolved = get_default_state_dir().resolve()
    assert resolved != USER_BRAIN_STATE
    assert not _is_inside(resolved, USER_BRAIN_STATE)


def test_brain_without_state_dir_stays_outside_user_data():
    brain = InfantApeBrain(headless=True, auto_save=False)
    base = Path(brain.persistence.base_dir).resolve()
    assert base != USER_BRAIN_STATE
    assert not _is_inside(base, USER_BRAIN_STATE)
