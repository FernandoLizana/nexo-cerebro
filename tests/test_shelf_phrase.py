"""The remembered phrase comes from the file, and a held file raises curiosity."""

from brain.collective_capacity import exclusive_mark
from brain.curiosity import compute_curiosity
from brain.body import BodyState
from brain.neurotransmitters import NeuromodulatorState
from services.presence.shelf import PDF_HEADER, split_excerpt


def test_pdf_mark_skips_the_canned_header() -> None:
    excerpt = f"{PDF_HEADER}\nThe kelp forest stores iodine in its blades."
    header, body = split_excerpt(excerpt)
    assert header == PDF_HEADER
    assert "kelp" in exclusive_mark(excerpt)
    assert "dejado" not in exclusive_mark(excerpt)
    assert body.startswith("The kelp")


def test_one_held_file_raises_curiosity_by_the_shelf_block() -> None:
    body = BodyState()
    mods = NeuromodulatorState()
    low = compute_curiosity(body, mods, unread_shelf=0)
    high = compute_curiosity(body, mods, unread_shelf=1)
    assert high == low + 0.08
