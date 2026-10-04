#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export CEREBRO_OLLAMA=0
export CEREBRO_SKIP_PROCESS_GUARD=1
PY="${ROOT}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then PY=python3; fi
"$PY" -u publication_finalization/scripts/run_publication_experiments.py --phase all --seeds 10 --steps 100 --profile compact
"$PY" -u publication_finalization/scripts/run_motor_audit.py || true
"$PY" -u publication_finalization/scripts/build_stats.py
"$PY" -u publication_finalization/figure_scripts/plot_publication_figures.py
"$PY" -u publication_finalization/scripts/pack_final.py
echo "Done. See publication_finalization/FINAL_VALIDATION_REPORT.md"
