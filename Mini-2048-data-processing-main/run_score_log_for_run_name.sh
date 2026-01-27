#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_score_log_for_run_name.sh --run-name NAME [options]

Options:
  --run-name NAME      run_name under ntuple_dat (required)
  --dat-root DIR       ntuple_dat root (default: /HDD/momiyama2/data/study/ntuple_dat)
  --out-root DIR       analysis_outputs root (default: /HDD/momiyama2/data/study/analysis_outputs)
  --output FILE        output filename (default: score_log.png)
  --split-nt           split NT4/NT6 into separate plots
USAGE
}

RUN_NAME=""
DAT_ROOT="/HDD/momiyama2/data/study/ntuple_dat"
OUT_ROOT="/HDD/momiyama2/data/study/analysis_outputs"
OUTPUT_FILE="score_log.png"
SPLIT_NT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name) RUN_NAME="$2"; shift 2;;
    --dat-root) DAT_ROOT="$2"; shift 2;;
    --out-root) OUT_ROOT="$2"; shift 2;;
    --output) OUTPUT_FILE="$2"; shift 2;;
    --split-nt) SPLIT_NT=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1" >&2; usage; exit 1;;
  esac
done

if [[ -z "$RUN_NAME" ]]; then
  echo "ERROR: --run-name is required." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/plot_score_log.py" \
  --run-name "$RUN_NAME" \
  --dat-root "$DAT_ROOT" \
  --out-root "$OUT_ROOT" \
  --output "$OUTPUT_FILE" \
  $( [[ "$SPLIT_NT" -eq 1 ]] && echo --split-nt )
