"""Voluntary link from the NEXO central to the fruit-fly model.

Does not import Brian 2 until a pulse is asked for, and does not start
if the connectivity parquet is missing. The 3D house is not involved.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

MAX_NEURONS = 3
MAX_MS = 200


def fly_root() -> Path:
    override = os.environ.get("NEXO_FLY_ROOT", "").strip()
    if override:
        return Path(override)
    escritorio = Path(__file__).resolve().parents[3]
    return escritorio / "mosca" / "brain_model"


def _first(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.is_file():
            return path
    return None


def status() -> dict[str, Any]:
    root = fly_root()
    code = root / "model.py"
    complete = _first(
        [
            root / "2023_03_23_completeness_630_final.csv",
            root / "Completeness_783.csv",
        ]
    )
    parquet = _first(list(root.glob("*.parquet")) + list(root.glob("Connectivity*.parquet")))
    missing = []
    if not code.is_file():
        missing.append("model.py")
    if complete is None:
        missing.append("completeness csv")
    if parquet is None:
        missing.append("connectivity parquet")
    return {
        "ok": not missing,
        "root": str(root),
        "code": code.is_file(),
        "completeness": str(complete) if complete else None,
        "connectivity": str(parquet) if parquet else None,
        "missing": missing,
        "note": "La casa 3D no se toca. Un pulso solo corre si el parquet está.",
    }


def pulse(neuron_ids: list[int], *, duration_ms: int = 100) -> dict[str, Any]:
    """One short activation. Fails closed if the fly model cannot run."""
    info = status()
    if not info["ok"]:
        return {"ok": False, "error": "fly model not ready", "status": info}
    ids = []
    for raw in neuron_ids[:MAX_NEURONS]:
        try:
            ids.append(int(raw))
        except (TypeError, ValueError):
            return {"ok": False, "error": "bad flywire id"}
    if not ids:
        return {"ok": False, "error": "no neurons"}
    ms = max(20, min(int(duration_ms), MAX_MS))
    root = fly_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from brian2 import ms as brian_ms
        import model as fly_model
    except ImportError as exc:
        return {"ok": False, "error": f"brian2 or model import failed: {exc}", "status": info}
    params = dict(fly_model.default_params)
    params["t_run"] = ms * brian_ms
    params["n_run"] = 1
    try:
        spikes = fly_model.run_trial(
            ids,
            [],
            [],
            info["completeness"],
            info["connectivity"],
            params,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:240], "status": info}
    return {
        "ok": True,
        "engine": "drosophila-brian2",
        "neurons": ids,
        "duration_ms": ms,
        "spike_keys": len(spikes),
        "status": info,
    }
