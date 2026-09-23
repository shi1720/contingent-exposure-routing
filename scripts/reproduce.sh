#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN="${CER_PYTHON:-python}"
"$PYTHON_BIN" -m pytest -q
"$PYTHON_BIN" scripts/run_synthetic.py
"$PYTHON_BIN" scripts/analyze_api.py
"$PYTHON_BIN" scripts/run_tail_checks.py
"$PYTHON_BIN" scripts/summarize.py
"$PYTHON_BIN" scripts/make_tables.py
"$PYTHON_BIN" scripts/make_figures.py
if command -v tectonic >/dev/null 2>&1; then
  (cd paper && tectonic main.tex)
  cp paper/main.pdf output/pdf/Gupta_Contingent_Exposure_Routing.pdf
fi
