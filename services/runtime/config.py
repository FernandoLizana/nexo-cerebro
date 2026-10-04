"""Load and merge CLI / file / env parameters for Swarm tools."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping


def load_params_file(path: Path | str | None) -> dict[str, Any]:
    """Load YAML or JSON parameter file. Empty dict if path is None."""
    if path is None:
        return {}
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"params file not found: {p}")
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        import yaml

        data = yaml.safe_load(text) or {}
    elif suffix == ".json":
        data = json.loads(text or "{}")
    else:
        # Try JSON first, then YAML.
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            import yaml

            data = yaml.safe_load(text) or {}
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"params file must be a mapping/object: {p}")
    return dict(data)


def load_params_json(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("--params must be a JSON object")
    return dict(data)


def env_overrides(prefix: str = "NEXO_") -> dict[str, Any]:
    """Pull simple overrides from env: NEXO_PORT=8765 -> {"port": "8765"} (stringy)."""
    out: dict[str, Any] = {}
    plen = len(prefix)
    for key, value in os.environ.items():
        if not key.startswith(prefix) or key == prefix:
            continue
        name = key[plen:].lower()
        if not name or name.startswith("secret") or name.endswith("_key"):
            continue
        out[name] = value
    return out


def merge_params(
    *layers: Mapping[str, Any] | None,
    allow: frozenset[str] | set[str] | None = None,
) -> dict[str, Any]:
    """
    Merge parameter layers left-to-right (later wins).
    If ``allow`` is set, drop unknown keys (fail-closed against surprise binds).
    """
    merged: dict[str, Any] = {}
    for layer in layers:
        if not layer:
            continue
        for k, v in layer.items():
            if v is None:
                continue
            if allow is not None and k not in allow:
                continue
            merged[k] = v
    return merged
