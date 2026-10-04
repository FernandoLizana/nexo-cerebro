"""Shared argparse helpers for config / params / background modes."""

from __future__ import annotations

import argparse
from pathlib import Path


def add_params_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="YAML/JSON file with default parameters (CLI flags override)",
    )
    parser.add_argument(
        "--params",
        default=None,
        help='Inline JSON object of overrides, e.g. \'{"seed":7,"port":8765}\'',
    )


def add_background_arguments(parser: argparse.ArgumentParser) -> None:
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--foreground",
        action="store_true",
        default=False,
        help="Run in the current terminal (default when neither mode is set)",
    )
    mode.add_argument(
        "--background",
        "--detach",
        dest="background",
        action="store_true",
        default=False,
        help="Opt-in: detach into a background process (writes pid + runtime record)",
    )
    parser.add_argument(
        "--pid-file",
        type=Path,
        default=None,
        help="Optional explicit pid file path (default: <data-dir>/<service>.pid)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Optional log path hint stored in the runtime record (child still uses stdout redirect if set via env)",
    )
