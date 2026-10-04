"""S1 Core Fortress — regression locks for NEXO Collective Swarm.

These tests MUST NOT change Core behavior. They freeze import surfaces,
local-only MessageBus semantics, package phase markers, and known P1 debt
so Swarm work cannot silently regress the scientific runtime.

Principle: NINGUNA FUNCIÓN DEL SWARM PUEDE COMPROMETER LA ESTABILIDAD DEL CORE.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import nexo_qa
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_fortress_nexo_qa_phase_is_p9() -> None:
    assert nexo_qa.__phase__ == "P9"
    assert nexo_qa.__version__ == "0.9.0-p9"
    assert nexo_qa.__enabled_by_default__ is False
    assert Path(nexo_qa.__file__).resolve() == (ROOT / "nexo_qa" / "__init__.py").resolve()


def test_fortress_critical_core_modules_import() -> None:
    """C2–C6, C8–C9, C16 import surface (does not require untracked P1 files)."""
    from nexo.core.clock import SimulationClock
    from nexo.core.messages import MessageBus
    from nexo.core.scheduler import CognitiveScheduler
    from nexo.core.state_store import StateStore
    from nexo.integrated_runtime import IntegratedRuntime
    from nexo.prefrontal.deliberation import PrefrontalDeliberator
    from nexo.random_streams import RandomStreams

    assert SimulationClock is not None
    assert StateStore is not None
    assert CognitiveScheduler is not None
    assert MessageBus is not None
    assert IntegratedRuntime is not None
    assert PrefrontalDeliberator is not None
    assert RandomStreams is not None


def test_fortress_message_bus_is_in_process_only() -> None:
    """C16: MessageBus must remain a local tick queue — never a network facade."""
    src = (ROOT / "nexo" / "core" / "messages.py").read_text(encoding="utf-8")
    forbidden = (
        "socket.",
        "http.client",
        "urllib.request",
        "requests.",
        "aiohttp",
        "websocket",
        "grpc",
    )
    for token in forbidden:
        assert token not in src, f"MessageBus must not reference {token!r}"


def test_fortress_pfc_run_accepts_action_schemas() -> None:
    """C7: PFC must accept ActionSchema catalogs (P1 contract complete)."""
    from nexo.prefrontal.deliberation import PrefrontalDeliberator

    params = inspect.signature(PrefrontalDeliberator.run).parameters
    assert "candidates" in params
    assert "action_schemas" in params


def test_fortress_p1_contract_files_are_tracked_modules() -> None:
    """C1: ActionSchema triad must exist as importable Core modules."""
    from nexo.core import action_schema, environment_protocol, legacy_action_adapter

    triad = [
        ROOT / "nexo" / "core" / "action_schema.py",
        ROOT / "nexo" / "core" / "environment_protocol.py",
        ROOT / "nexo" / "core" / "legacy_action_adapter.py",
    ]
    for path in triad:
        assert path.is_file(), f"missing {path}"
        ast.parse(path.read_text(encoding="utf-8"))
    assert action_schema.ActionSchema is not None
    assert environment_protocol.EnvironmentProtocol is not None
    assert legacy_action_adapter.schema_from_legacy_action is not None


def test_fortress_no_product_package_on_import_path_for_science() -> None:
    """SaaS product must not auto-load when importing scientific nexo_qa."""
    import sys

    product_loaded = any(
        k == "nexo_qa.product" or k.startswith("nexo_qa.product.") for k in sys.modules
    )
    assert product_loaded is False


def test_fortress_mock_world_and_population_seed_helpers() -> None:
    from nexo_qa.population.seeds import derive_child_seed, derive_run_id
    from nexo_qa.testing.mock_world import MockWorld

    world = MockWorld()
    assert callable(world.available_actions)
    seed_a = derive_child_seed(
        42,
        cohort_id="c0",
        task_id="t0",
        sample_index=0,
        persona_id="p0",
        condition_set_id="baseline",
    )
    seed_b = derive_child_seed(
        42,
        cohort_id="c0",
        task_id="t0",
        sample_index=0,
        persona_id="p0",
        condition_set_id="baseline",
    )
    assert seed_a == seed_b
    run_id = derive_run_id(
        "spec",
        "c0",
        "t0",
        "p0",
        seed_a,
        "baseline",
        0,
    )
    assert isinstance(run_id, str) and run_id


def test_fortress_browser_policy_defaults_are_restrictive() -> None:
    from nexo_qa.browser.policy import BrowserPolicy

    policy = BrowserPolicy()
    assert hasattr(policy, "is_allowed_url")
    assert policy.is_allowed_url("http://127.0.0.1/") is True
    assert policy.is_allowed_url("https://evil.example/") is False

@pytest.mark.integration
def test_fortress_security_deny_tokens_not_in_planned_swarm_surface() -> None:
    """Static deny-list for node packages: tokens may appear only as rejections."""
    candidates = [
        ROOT / "services" / "node",
        ROOT / "services" / "coordinator",
        ROOT / "services" / "memory",
        ROOT / "services" / "experience",
        ROOT / "services" / "knowledge",
        ROOT / "services" / "simulator",
        ROOT / "services" / "dashboard",
        ROOT / "services" / "packaging",
        ROOT / "services" / "lab",
        ROOT / "services" / "learning",
        ROOT / "nexo_swarm",
    ]
    # These strings are allowed inside explicit deny/reject lists, not as features.
    forbidden_feature_snippets = (
        "keylogger",
        "credential harvest",
        "self-replicat",
        "privilege escalation",
        "disable antivirus",
    )
    for base in candidates:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for snippet in forbidden_feature_snippets:
                assert snippet.lower() not in text, f"{path} contains forbidden {snippet!r}"
            # EXECUTE_SHELL may exist only as a forbidden prefix / rejection path.
            if "execute_shell" in text and "forbidden" not in text and "allowlist" not in text:
                raise AssertionError(f"{path} mentions EXECUTE_SHELL outside allowlist/deny context")
