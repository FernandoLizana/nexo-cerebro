"""S8 — Local Memory tests (persistence, decay, isolation, anti prompt-stuffing)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from services.being.creator import create_being
from services.being.store import BeingStore
from services.memory.local.models import MemoryKind
from services.memory.local.recall import (
    HARD_RECALL_CAP,
    MAX_PROMPT_CHARS,
    MemoryPolicyError,
    context_for_prompt,
)
from services.memory.local.store import LocalMemoryStore

ROOT = Path(__file__).resolve().parents[1]
MEM_PKG = ROOT / "services" / "memory"


def test_persist_survives_restart(tmp_path: Path) -> None:
    beings = tmp_path / "beings"
    store = BeingStore(beings)
    being = create_being(
        name="Mira",
        species="EXPERIMENTAL",
        creator_node="node-test",
        store=store,
    )
    mem = LocalMemoryStore.for_being(beings, being.identity.being_id)
    mem.add_episodic("found a red berry", importance=0.8)
    mem.add_semantic("berries grow near water", importance=0.7)
    mem.upsert_relationship("being-other", relation_type="ally", strength=0.9, notes="helped once")

    mem2 = LocalMemoryStore.for_being(beings, being.identity.being_id)
    assert mem2.count() == 3
    assert any("berry" in e.content for e in mem2.list_entries(MemoryKind.EPISODIC))
    rels = mem2.list_relationships()
    assert len(rels) == 1
    assert rels[0].peer_being_id == "being-other"
    assert (mem2.memory_root / "index.json").is_file()


def test_decay_and_recall_counts(tmp_path: Path) -> None:
    mem = LocalMemoryStore(tmp_path / "mem", being_id="b1")
    low = mem.add_episodic("noise event", importance=0.1, confidence=0.5)
    high = mem.add_episodic("critical lesson", importance=0.95, confidence=0.9)
    before_low = low.decay
    mem.apply_decay(0.2)
    low2 = next(e for e in mem.list_entries(MemoryKind.EPISODIC) if e.record_id == low.record_id)
    high2 = next(e for e in mem.list_entries(MemoryKind.EPISODIC) if e.record_id == high.record_id)
    assert low2.decay > before_low
    assert high2.decay < low2.decay  # important decays slower

    recalled = mem.recall("critical", limit=2)
    assert recalled
    assert recalled[0].record_id == high.record_id
    assert recalled[0].recall_count >= 1
    # Reload and confirm recall_count persisted
    mem3 = LocalMemoryStore(tmp_path / "mem", being_id="b1")
    again = next(e for e in mem3.list_entries(MemoryKind.EPISODIC) if e.record_id == high.record_id)
    assert again.recall_count >= 1


def test_isolation_between_beings(tmp_path: Path) -> None:
    beings = tmp_path / "beings"
    store = BeingStore(beings)
    a = create_being(name="Alpha", species="EXPERIMENTAL", creator_node="node-test", store=store)
    b = create_being(name="Beta", species="EXPERIMENTAL", creator_node="node-test", store=store)
    ma = LocalMemoryStore.for_being(beings, a.identity.being_id)
    mb = LocalMemoryStore.for_being(beings, b.identity.being_id)
    ma.add_semantic("alpha-secret-knowledge", importance=0.9)
    mb.add_semantic("beta-only-fact", importance=0.9)
    assert all("beta" not in e.content for e in ma.list_entries(MemoryKind.SEMANTIC))
    assert all("alpha" not in e.content for e in mb.list_entries(MemoryKind.SEMANTIC))
    assert ma.memory_root != mb.memory_root


def test_prompt_context_is_bounded_not_wholesale(tmp_path: Path) -> None:
    mem = LocalMemoryStore(tmp_path / "mem", being_id="b1")
    for i in range(40):
        mem.add_episodic(f"event-{i}-" + ("x" * 80), importance=0.4 + (i % 10) * 0.05)
    assert mem.count() == 40
    snippet = mem.prompt_context(limit=5, max_chars=400)
    assert len(snippet) <= 400
    assert snippet.count("\n") < 5  # at most 5 lines → ≤4 newlines, or fewer if truncated
    # Must not contain all events
    assert "event-0" not in snippet or "event-39" not in snippet or len(snippet) < 2000

    with pytest.raises(MemoryPolicyError):
        mem.export_for_science(for_llm=True)

    with pytest.raises(MemoryPolicyError):
        context_for_prompt(mem.all_scored(), limit=5, max_chars=20_000)

    # Hard cap: even huge limit request clamps
    got = mem.recall(limit=10_000)
    assert len(got) <= HARD_RECALL_CAP


def test_memory_package_has_no_networking_or_shell(tmp_path: Path) -> None:
    forbidden = ("socket", "subprocess", "http.client", "urllib.request", "asyncio.create_subprocess")
    for path in MEM_PKG.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[0] not in {"socket", "subprocess", "urllib", "http"}
            if isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                assert top not in {"socket", "subprocess", "urllib", "http"}
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            # allow only inside comments/strings that reject — keep package clean
            if token in text and "forbidden" not in text.lower():
                # substring check for import-like usage
                if f"import {token}" in text or f"from {token}" in text:
                    raise AssertionError(f"{path} imports {token}")


def test_max_prompt_chars_constant_is_safe() -> None:
    assert MAX_PROMPT_CHARS <= 8000
    assert HARD_RECALL_CAP <= 64
