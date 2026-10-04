"""H2 — auditoría agency con certificados causales v2."""

from __future__ import annotations

import argparse
import json

from experiments.personal.h1_runner import export_payload, run_h1_interactive
from nexo.integrated_runtime import _repo_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="experiments.personal.run_h2_agency_audit")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--ticks", type=int, default=80)
    args = parser.parse_args(argv)

    root = _repo_root()
    cfg = root / "configs/nexo/integrated_v90.yaml"
    payload = run_h1_interactive(seed=args.seed, ticks=args.ticks, config_path=cfg)
    agency = payload.get("agency_audit", {})
    causal = payload.get("causal_certificates", {})

    result = {
        "seed": args.seed,
        "ticks": args.ticks,
        "profile": "integrated_v90",
        "encoding": payload.get("encoding", {}),
        "causal_certificate": causal,
        "agency_audit": agency,
        "hypothesis_h2": {
            "agency_valid_rate": agency.get("agency_score", 0.0),
            "certificate_valid_rate": agency.get("certificate_score", 0.0),
            "motor_agreement_rate": agency.get("motor_agreement_rate", 0.0),
            "valid_certificates": agency.get("valid_certificates", 0),
        },
    }
    out = root / "results" / "personal" / "H2_agency" / f"h2_agency_audit_seed{args.seed}.json"
    summary = export_payload(result, out)
    print(json.dumps({**summary, "hypothesis_h2": result["hypothesis_h2"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
