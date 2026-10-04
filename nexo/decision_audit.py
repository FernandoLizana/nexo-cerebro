"""Auditoría AST + regex de escrituras a choice_key."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

_FORBIDDEN_REGEX_IMPORT = None  # lazy

PRIMARY_WRITER_FILE = "deliberation.py"
APPROVED_WRITER_SYMBOL = "brain.deliberation.PrefrontalDeliberation.run"


@dataclass(frozen=True)
class AgencyViolation:
    path: str
    line: int
    text: str
    reason: str


class _ChoiceKeyAssignVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.violations: list[AgencyViolation] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Attribute) and target.attr == "choice_key":
                if not self.rel_path.endswith(PRIMARY_WRITER_FILE):
                    self.violations.append(
                        AgencyViolation(
                            self.rel_path,
                            node.lineno,
                            "choice_key assignment",
                            "AST: asignación a choice_key fuera de deliberation.py",
                        )
                    )
        self.generic_visit(node)


def _iter_brain_py(brain_dir: Path) -> Iterable[Path]:
    if not brain_dir.is_dir():
        return
    for path in sorted(brain_dir.rglob("*.py")):
        if path.name.startswith("_"):
            continue
        yield path


def scan_brain_tree(brain_dir: Path | None = None) -> dict[str, Any]:
    from nexo.paths import repo_root

    root = brain_dir or (repo_root() / "brain")
    if not root.is_dir():
        return {
            "status": "audit_incomplete",
            "ok": False,
            "violations": [],
            "files_scanned": 0,
            "assignments_found": 0,
            "approved_writers": [APPROVED_WRITER_SYMBOL],
            "parse_errors": [{"path": str(root), "error": "brain_directory_missing"}],
            "missing_required_files": ["brain/"],
            "limitations": ["No se pudo escanear: brain/ ausente"],
        }

    deliberation = root / PRIMARY_WRITER_FILE
    missing_required: list[str] = []
    if not deliberation.is_file():
        missing_required.append(f"brain/{PRIMARY_WRITER_FILE}")

    violations: list[AgencyViolation] = []
    parse_errors: list[dict[str, str]] = []
    files_scanned = 0
    import re

    forbidden = (
        re.compile(r"\bdeliberation\.last\.choice_key\s*="),
        re.compile(r"\bbrain\.deliberation\.last\.choice_key\s*="),
        re.compile(r"\bself\.last\.choice_key\s*="),
    )

    for path in _iter_brain_py(root):
        files_scanned += 1
        rel = path.relative_to(root.parent).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), start=1):
            if path.name == PRIMARY_WRITER_FILE:
                continue
            for pat in forbidden:
                if pat.search(line):
                    violations.append(AgencyViolation(rel, i, line.strip()[:120], "regex"))
        try:
            tree = ast.parse(text, filename=str(path))
            visitor = _ChoiceKeyAssignVisitor(rel)
            visitor.visit(tree)
            violations.extend(visitor.violations)
        except SyntaxError as exc:
            parse_errors.append({"path": rel, "error": str(exc)})

    status = "audit_pass"
    ok = True
    if missing_required or files_scanned == 0:
        status = "audit_incomplete"
        ok = False
    elif parse_errors:
        status = "audit_incomplete"
        ok = False
    elif violations:
        status = "audit_fail"
        ok = False

    return {
        "status": status,
        "ok": ok,
        "violations": [v.__dict__ for v in violations],
        "files_scanned": files_scanned,
        "assignments_found": len(violations),
        "approved_writers": [APPROVED_WRITER_SYMBOL],
        "parse_errors": parse_errors,
        "missing_required_files": missing_required,
        "primary_writer": f"brain/{PRIMARY_WRITER_FILE}",
        "limitations": [
            "No detecta setattr dinámico en todos los casos",
            "DeliberationResult(...) directo fuera de deliberation no siempre detectado",
        ],
    }
