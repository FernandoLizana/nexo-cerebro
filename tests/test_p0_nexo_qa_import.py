"""P0/P1 smoke: importing nexo and nexo_qa must not break the scientific core."""

from __future__ import annotations


def test_p0_import_nexo_and_nexo_qa() -> None:
    import nexo
    import nexo_qa

    assert nexo.__version__
    assert nexo_qa.__phase__ == "P9"
    assert nexo_qa.__enabled_by_default__ is False
