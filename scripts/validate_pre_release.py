#!/usr/bin/env python3
"""Pre-release validation gate for NEXO Collective Swarm (local / Docker).

Checks: fortress + S2–S17 tests, security static scan, packaging policy,
entry points, SaaS residue absence, README/docs presence.
Exit 0 only if all gates pass.
"""

from __future__ import annotations

import ast
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SERVICES = ROOT / "services"
PROTOCOLS = ROOT / "protocols"
PACKAGING = ROOT / "packaging"

FORBIDDEN_IMPORT_ROOTS = frozenset(
    {"socket", "subprocess", "paramiko", "requests", "aiohttp", "httpx", "telnetlib"}
)
# Packages that may mention socket only via ssl stdlib for TLS policy (lab)
ALLOW_SSL_ONLY = frozenset({"lab"})

SWARM_TEST_FILES = [
    "tests/test_swarm_core_fortress.py",
    "tests/test_s2_node_runtime.py",
    "tests/test_s3_being_model.py",
    "tests/test_s4_creature_engine.py",
    "tests/test_s5_textworld.py",
    "tests/test_s6_interaction_protocol.py",
    "tests/test_s7_coordinator.py",
    "tests/test_s8_local_memory.py",
    "tests/test_s9_experience_store.py",
    "tests/test_s10_knowledge_graph.py",
    "tests/test_s11_swarm_simulator.py",
    "tests/test_s12_dashboard.py",
    "tests/test_s13_windows_packaging.py",
    "tests/test_s14_debian_packaging.py",
    "tests/test_s15_multi_device_lab.py",
    "tests/test_s16_collective_learning.py",
    "tests/test_s17_federated_learning.py",
]

REQUIRED_DOCS = [
    "README.md",
    "ARCHITECTURE.md",
    "ROADMAP.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "docs/planes/NEXO_SWARM_MASTER_PLAN.md",
    "docs/NEXO_SWARM_SECURITY_MODEL.md",
    "docs/NEXO_SWARM_ARCHITECTURE.md",
    "docs/experiments/README.md",
    "packaging/windows/README.md",
    "packaging/debian/README.md",
]

REQUIRED_ENTRY_POINTS = [
    "nexo-node",
    "nexo-being",
    "nexo-creature",
    "nexo-textworld",
    "nexo-coordinator",
    "nexo-memory",
    "nexo-experience",
    "nexo-knowledge",
    "nexo-simulator",
    "nexo-dashboard",
    "nexo-winpack",
    "nexo-debpack",
    "nexo-lab",
    "nexo-learn",
    "nexo-fl",
    "nexo-ctl",
    "nexo-lab-gateway",
]

SAAS_PATHS = [
    ROOT / "nexo_qa" / "product",
    ROOT / "data" / "product.db",
    ROOT / "PROMPT_PORTAL_CLIENTE_NEXO_HYPER.md",
    ROOT / "NEXO_ECOSYSTEM_MASTER_ARTIFACT.md",
]


class GateFailure(Exception):
    pass


def _ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def _fail(msg: str) -> None:
    raise GateFailure(msg)


def gate_docs() -> None:
    print("\n== Docs ==")
    for rel in REQUIRED_DOCS:
        path = ROOT / rel
        if not path.is_file():
            _fail(f"missing required doc: {rel}")
        if path.stat().st_size < 80:
            _fail(f"doc too thin: {rel}")
        _ok(rel)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required_cues = [
        "experimental distributed cognitive-agent laboratory",
        "does **not** claim",
        "SECURITY.md",
        "nexo-lab",
        "Hard prohibitions",
        "S17",
        "Kill switch",
        "validate_pre_release",
        "Docker",
        "nexo-fl",
    ]
    missing = [c for c in required_cues if c not in readme]
    if missing:
        _fail(f"README missing required cues: {missing}")
    _ok("README framing cues")

    checklist = ROOT / "docs" / "validation" / "PRE_RELEASE_CHECKLIST.md"
    if not checklist.is_file():
        _fail("missing docs/validation/PRE_RELEASE_CHECKLIST.md")
    _ok("docs/validation/PRE_RELEASE_CHECKLIST.md")

    docker_doc = ROOT / "docs" / "DOCKER_VALIDATION.md"
    if not docker_doc.is_file():
        _fail("missing docs/DOCKER_VALIDATION.md")
    _ok("docs/DOCKER_VALIDATION.md")
    if not (ROOT / "Dockerfile").is_file():
        _fail("missing Dockerfile")
    _ok("Dockerfile")
    if not (ROOT / "docker-compose.validate.yml").is_file():
        _fail("missing docker-compose.validate.yml")
    _ok("docker-compose.validate.yml")


def gate_saas_absent() -> None:
    print("\n== SaaS residue ==")
    for path in SAAS_PATHS:
        if path.exists():
            _fail(f"SaaS residue still present: {path.relative_to(ROOT)}")
        _ok(f"absent: {path.relative_to(ROOT)}")


def gate_security_static() -> None:
    print("\n== Security static scan (services/protocols/packaging) ==")
    roots = [SERVICES, PROTOCOLS, PACKAGING]
    offenders: list[str] = []
    forbidden_snippets = (
        "keylogger",
        "credential harvest",
        "self-replicat",
        "privilege escalation",
        "disable antivirus",
    )
    for base in roots:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            lower = text.lower()
            for snippet in forbidden_snippets:
                if snippet in lower:
                    offenders.append(f"{path}: forbidden snippet {snippet!r}")
            # EXECUTE_SHELL only in deny contexts
            if "execute_shell" in lower and "forbidden" not in lower and "allowlist" not in lower and "fault" not in path.name.lower():
                offenders.append(f"{path}: EXECUTE_SHELL outside deny/fault context")
            try:
                tree = ast.parse(text)
            except SyntaxError as exc:
                offenders.append(f"{path}: syntax error {exc}")
                continue
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module.split(".")[0]]
                for name in names:
                    if name in FORBIDDEN_IMPORT_ROOTS:
                        # dashboard/flask uses no socket directly; lab may use ssl only
                        rel = path.relative_to(ROOT).as_posix()
                        if name == "socket" and "/lab/" in rel:
                            offenders.append(f"{path}: unexpected socket import in lab")
                        elif name != "ssl":
                            offenders.append(f"{path}: forbidden import {name}")
    if offenders:
        _fail("security scan failures:\n  - " + "\n  - ".join(offenders[:40]))
    _ok("no forbidden imports/snippets in Swarm surface")

    # Packaging policies
    from services.packaging.windows.silent_policy import reject_silent_flags, SilentInstallError
    from services.packaging.debian.policy import packaging_policy, assert_maintainer_script_safe

    try:
        reject_silent_flags(["/S"])
        _fail("silent flag /S was not rejected")
    except SilentInstallError:
        _ok("Windows silent /S rejected")

    pol = packaging_policy()
    if pol.get("forced_root_persistence") or pol.get("system_service_enabled_by_default"):
        _fail("Debian policy allows forced root persistence")
    _ok("Debian policy: no forced root persistence")
    for name in ("postinst", "prerm", "postrm"):
        assert_maintainer_script_safe((PACKAGING / "debian" / name).read_text(encoding="utf-8"))
    _ok("Debian maintainer scripts safe")


def gate_entry_points() -> None:
    print("\n== Entry points ==")
    eps: dict[str, str] = {}
    # Prefer pyproject.toml as source of truth (works even if editable install is stale)
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover
        import tomli as tomllib  # type: ignore
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    eps = dict(data.get("project", {}).get("scripts", {}) or {})
    for name in REQUIRED_ENTRY_POINTS:
        if name not in eps:
            _fail(f"missing entry point in pyproject.toml: {name}")
        _ok(f"{name} -> {eps[name]}")
    # Optional: confirm installed dist exposes them when available
    try:
        dist = importlib.metadata.distribution("nexo-cerebro")
        installed = {ep.name for ep in dist.entry_points if ep.group == "console_scripts"}
        missing_installed = [n for n in REQUIRED_ENTRY_POINTS if n not in installed]
        if missing_installed:
            _fail(
                "editable install missing scripts "
                f"{missing_installed}; run: pip install -e '.[dev]'"
            )
        _ok("editable install exposes all console scripts")
    except importlib.metadata.PackageNotFoundError:
        print("  WARN  nexo-cerebro not installed; skipped install check (pyproject OK)")


def gate_smoke_clis() -> None:
    print("\n== CLI smoke ==")
    checks = [
        [sys.executable, "-m", "services.packaging.windows.cli", "pipeline"],
        [sys.executable, "-m", "services.packaging.debian.cli", "policy"],
        [sys.executable, "-m", "services.lab.cli", "tls-policy"],
        [sys.executable, "-m", "services.ctl.cli", "list"],
        [sys.executable, "-m", "services.lab_gateway.cli", "--help"],
        [sys.executable, "-m", "services.learning.federated.cli", "status"],  # should fail without flags
    ]
    # winpack/debpack/lab/ctl should succeed
    for cmd in checks[:5]:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if proc.returncode != 0:
            _fail(f"CLI failed ({cmd}): {proc.stderr or proc.stdout}")
        _ok(" ".join(cmd[-2:]))
    # nexo-fl without opt-in must fail closed
    proc = subprocess.run(checks[5], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode == 0:
        _fail("nexo-fl status succeeded without --enable-research (must fail closed)")
    _ok("nexo-fl fails closed without research flags")

    # Lab rehearsal
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "services.lab.cli",
            "rehearse",
            "--root",
            str(ROOT / "artifacts" / "pre_release_lab"),
            "--seed",
            "11",
            "--lab-name",
            "pre-release",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        _fail(f"nexo-lab rehearse failed: {proc.stderr or proc.stdout}")
    _ok("nexo-lab rehearse")


def gate_pytest() -> None:
    print("\n== Pytest Swarm S2–S17 + fortress ==")
    cmd = [sys.executable, "-m", "pytest", *SWARM_TEST_FILES, "-q", "--tb=line"]
    proc = subprocess.run(cmd, cwd=ROOT)
    if proc.returncode != 0:
        _fail("pytest Swarm suite failed")
    _ok(f"{len(SWARM_TEST_FILES)} test modules")


def main() -> int:
    print("NEXO pre-release validation")
    print(f"root: {ROOT}")
    report: dict = {"ok": False, "gates": []}
    try:
        gate_docs()
        gate_saas_absent()
        gate_security_static()
        gate_entry_points()
        gate_smoke_clis()
        gate_pytest()
    except GateFailure as exc:
        print(f"\nFAIL: {exc}")
        report["error"] = str(exc)
        out = ROOT / "artifacts" / "PRE_RELEASE_VALIDATION.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 1

    report["ok"] = True
    report["message"] = "all pre-release gates passed"
    out = ROOT / "artifacts" / "swarm" / "PRE_RELEASE_VALIDATION.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("\nALL GATES PASSED")
    print(f"report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
