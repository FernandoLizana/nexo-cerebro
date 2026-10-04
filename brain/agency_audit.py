"""
Auditoría estática de agency — item 100.

Verifica que ningún módulo en ``brain/`` escriba ``choice_key`` de deliberación
fuera de ``deliberation.py``. Solo lectura / parámetros / otros dataclasses OK.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class AgencyViolation:
    path: str
    line: int
    text: str
    reason: str


# Escrituras directas al resultado de deliberación (PFC).
_FORBIDDEN = (
    re.compile(r"\bdeliberation\.last\.choice_key\s*="),
    re.compile(r"\bbrain\.deliberation\.last\.choice_key\s*="),
    re.compile(r"\bself\.last\.choice_key\s*="),
    re.compile(r"\bDeliberationResult\s*\("),
)

# Único módulo autorizado a construir DeliberationResult y asignar last.
_PRIMARY_WRITER = "deliberation.py"


def _iter_brain_py_files(brain_dir: Path) -> Iterable[Path]:
    for path in sorted(brain_dir.rglob("*.py")):
        if path.name.startswith("_"):
            continue
        yield path


def scan_brain_agency(*, brain_dir: Path | None = None) -> list[AgencyViolation]:
    root = brain_dir or Path(__file__).resolve().parent
    violations: list[AgencyViolation] = []

    for path in _iter_brain_py_files(root):
        rel = path.name
        text = path.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pat in _FORBIDDEN:
                if not pat.search(line):
                    continue
                if rel == _PRIMARY_WRITER:
                    continue
                reason = "DeliberationResult construction" if "DeliberationResult" in pat.pattern else "direct choice_key write"
                violations.append(
                    AgencyViolation(
                        path=str(path.relative_to(root.parent)),
                        line=i,
                        text=stripped[:120],
                        reason=reason,
                    )
                )
    return violations


def audit_summary(*, brain_dir: Path | None = None) -> dict:
    violations = scan_brain_agency(brain_dir=brain_dir)
    return {
        "ok": len(violations) == 0,
        "violations": [
            {"path": v.path, "line": v.line, "text": v.text, "reason": v.reason} for v in violations
        ],
        "primary_writer": f"brain/{_PRIMARY_WRITER}",
        "agency_note": "Only PrefrontalDeliberation.run assigns deliberation.last.choice_key",
    }
