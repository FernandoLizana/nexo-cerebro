#!/usr/bin/env python3
"""Genera inventario, grafo de dependencias y datos para auditoría arquitectónica."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("brain", "nexo", "experiments", "tests", "scripts", "configs")
SKIP_PARTS = {".venv", "__pycache__", "artifacts", "publication_finalization", "dist", "node_modules"}


def _py_files(base: Path) -> list[Path]:
    out: list[Path] = []
    if not base.is_dir():
        return out
    for p in base.rglob("*.py"):
        if any(x in p.parts for x in SKIP_PARTS):
            continue
        out.append(p)
    return sorted(out)


def _module_name(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    return ".".join(rel.parts)


def _analyze_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {"module": _module_name(path), "parse_error": str(exc), "files": [str(path.relative_to(ROOT))]}
    classes: list[str] = []
    functions: list[str] = []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
            functions.append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            imports.append(mod)
    rng_hits = []
    for pat in ("np.random", "random.random", "random.seed", "time.time", "datetime.now"):
        if pat in text:
            rng_hits.append(pat)
    return {
        "module": _module_name(path),
        "files": [str(path.relative_to(ROOT).as_posix())],
        "classes": classes[:40],
        "functions": [f for f in functions if not f.startswith("_")][:40],
        "imports": sorted(set(imports))[:60],
        "imported_by": [],
        "randomness": rng_hits,
        "time_dependencies": [h for h in rng_hits if "time" in h or "datetime" in h],
        "integration_status": "legacy_brain" if path.parts[0] == "brain" else "nexo_infra",
        "risks": [],
    }


def main() -> int:
    modules: dict[str, dict] = {}
    for d in SCAN_DIRS:
        for f in _py_files(ROOT / d):
            rec = _analyze_file(f)
            modules[rec["module"]] = rec

    import_graph: dict[str, list[str]] = defaultdict(list)
    for mod, rec in modules.items():
        for imp in rec.get("imports", []):
            if imp.startswith("brain") or imp.startswith("nexo"):
                import_graph[mod].append(imp)

    reverse: dict[str, list[str]] = defaultdict(list)
    for src, targets in import_graph.items():
        for t in targets:
            reverse[t].append(src)

    for mod, rec in modules.items():
        rec["imported_by"] = sorted(set(reverse.get(mod, [])))[:30]

    inventory = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "module_count": len(modules),
        "modules": list(modules.values()),
    }
    graph = {
        "generated_at": inventory["generated_at"],
        "edges": [{"source": s, "target": t} for s, ts in import_graph.items() for t in ts],
        "node_count": len(modules),
        "edge_count": sum(len(v) for v in import_graph.values()),
    }

    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "NEXO_MODULE_INVENTORY.json").write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (reports / "NEXO_DEPENDENCY_GRAPH.json").write_text(
        json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    baseline: dict = {"generated_at": inventory["generated_at"]}
    for cmd in (
        ["git", "rev-parse", "HEAD"],
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests/"],
    ):
        try:
            out = subprocess.check_output(cmd, cwd=ROOT, text=True, timeout=180, stderr=subprocess.STDOUT)
            baseline[" ".join(cmd[:3])] = out.strip()[-500:]
        except Exception as exc:
            baseline[" ".join(cmd[:3])] = f"ERROR: {exc}"

    (reports / "NEXO_BASELINE_COMMANDS.json").write_text(
        json.dumps(baseline, indent=2), encoding="utf-8"
    )
    print(json.dumps({"modules": len(modules), "edges": graph["edge_count"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
