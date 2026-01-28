#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_plot_score_log_mean.sh --run-name NAME [options]

Options:
  --run-name NAME       run_name under ntuple_dat (required)
  --ntuple-dat-root DIR ntuple_dat root (default: /HDD/momiyama2/data/study/ntuple_dat)
  --tuples LIST         comma-separated tuples (default: 4,6)
  --sym-list LIST       comma-separated sym list (default: sym,notsym)
  --x-axis update|cpu   x-axis (default: update)
  --output-dir DIR      output dir (default: analysis_outputs/<run_name>/score_log)
  --file-prefix NAME    output filename prefix (default: score_log_mean)
USAGE
}

RUN_NAME=""
NTUPLE_DAT_ROOT="/HDD/momiyama2/data/study/ntuple_dat"
TUPLES="4,6"
SYM_LIST="sym,notsym"
X_AXIS="update"
OUTPUT_DIR=""
FILE_PREFIX="score_log_mean"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name) RUN_NAME="$2"; shift 2;;
    --ntuple-dat-root) NTUPLE_DAT_ROOT="$2"; shift 2;;
    --tuples) TUPLES="$2"; shift 2;;
    --sym-list) SYM_LIST="$2"; shift 2;;
    --x-axis) X_AXIS="$2"; shift 2;;
    --output-dir) OUTPUT_DIR="$2"; shift 2;;
    --file-prefix) FILE_PREFIX="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1"; usage; exit 1;;
  esac
done

if [[ -z "$RUN_NAME" ]]; then
  echo "ERROR: --run-name is required" >&2
  exit 1
fi

SCRIPT_DIR="/HDD/momiyama2/repo/training"
PY="$SCRIPT_DIR/plot_score_log_mean.py"

args=(
  --run-name "$RUN_NAME"
  --ntuple-dat-root "$NTUPLE_DAT_ROOT"
  --tuples "$TUPLES"
  --sym-list "$SYM_LIST"
  --x-axis "$X_AXIS"
  --file-prefix "$FILE_PREFIX"
)

if [[ -n "$OUTPUT_DIR" ]]; then
  args+=(--output-dir "$OUTPUT_DIR")
fi

python3 "$PY" "${args[@]}"
