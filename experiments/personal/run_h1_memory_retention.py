"""H1.3 — retención a largo plazo: delay + lesión + tres canales de recall."""

from __future__ import annotations

import argparse
import json

from experiments.personal.h1_runner import export_payload, run_h1_retention
from nexo.integrated_runtime import _repo_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="experiments.personal.run_h1_memory_retention")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--acquisition-ticks", type=int, default=0, help="0 = 288 (24h)")
    parser.add_argument("--delay-ticks", type=int, default=48)
    parser.add_argument("--probe-ticks", type=int, default=24)
    args = parser.parse_args(argv)

    payload = run_h1_retention(
        seed=args.seed,
        acquisition_ticks=args.acquisition_ticks or None,
        delay_ticks=args.delay_ticks,
        probe_ticks=args.probe_ticks,
    )
    out = _repo_root() / "results" / "personal" / "H1_memory" / f"h1_retention_seed{args.seed}.json"
    summary = export_payload(payload, out)
    print(
        json.dumps(
            {**summary, "retention_summary": payload["retention_summary"]},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
