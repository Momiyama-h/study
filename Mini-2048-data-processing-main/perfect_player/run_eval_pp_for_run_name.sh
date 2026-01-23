#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_eval_pp_for_run_name.sh --run-name NAME [options]

Options:
  --run-name NAME     run_name under board_data (required)
  --board-root PATH   board_data root (default: ../board_data)
  --output-mode MODE  output location: per-nt (default) or pp
  --force             overwrite existing eval files
  -h, --help         show this help
USAGE
}

RUN_NAME=""
BOARD_ROOT=""
OUTPUT_MODE="per-nt"
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name) RUN_NAME="$2"; shift 2;;
    --board-root) BOARD_ROOT="$2"; shift 2;;
    --output-mode) OUTPUT_MODE="$2"; shift 2;;
    --force) FORCE=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1"; usage; exit 1;;
  esac
done

if [[ -z "$RUN_NAME" ]]; then
  echo "ERROR: --run-name is required." >&2
  exit 1
fi
if [[ "$OUTPUT_MODE" != "per-nt" && "$OUTPUT_MODE" != "pp" ]]; then
  echo "ERROR: --output-mode must be 'per-nt' or 'pp'." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -z "$BOARD_ROOT" ]]; then
  BOARD_ROOT="$SCRIPT_DIR/../board_data"
fi

# Compile if missing
if [ ! -x "$SCRIPT_DIR/eval_state_pp" ]; then
  ( cd "$SCRIPT_DIR" && g++ eval_state.cpp -O2 -std=c++20 -mcmodel=large -o eval_state_pp )
fi
if [ ! -x "$SCRIPT_DIR/eval_after_state_pp" ]; then
  ( cd "$SCRIPT_DIR" && g++ eval_after_state.cpp -O2 -std=c++20 -mcmodel=large -o eval_after_state_pp )
fi

TARGET_ROOT="$BOARD_ROOT/$RUN_NAME"
if [ ! -d "$TARGET_ROOT" ]; then
  echo "ERROR: run_name directory not found: $TARGET_ROOT" >&2
  exit 1
fi

count=0
while IFS= read -r -d '' d; do
  case "$d" in
    "$BOARD_ROOT"/*) ;;
    *)
      echo "WARN: skip (outside board_root): $d" >&2
      continue
      ;;
  esac
  rel="${d#$BOARD_ROOT/}"
  safe="${rel//\//__}"
  safe="${safe//\\/__}"
  out_state="$BOARD_ROOT/PP/eval-state-${safe}.txt"
  out_after="$BOARD_ROOT/PP/eval-after-state-${safe}.txt"
  local_state="$d/eval-state.txt"
  local_after="$d/eval-after-state.txt"

  if [ "$OUTPUT_MODE" = "per-nt" ]; then
    if [ "$FORCE" -eq 0 ] && [ -f "$local_state" ] && [ -f "$local_after" ]; then
      continue
    fi
  else
    if [ "$FORCE" -eq 0 ] && [ -f "$out_state" ] && [ -f "$out_after" ]; then
      continue
    fi
  fi

  ( cd "$SCRIPT_DIR" && ./eval_state_pp "$rel" )
  ( cd "$SCRIPT_DIR" && ./eval_after_state_pp "$rel" )
  if [ "$OUTPUT_MODE" = "per-nt" ]; then
    mv -f "$out_state" "$local_state"
    mv -f "$out_after" "$local_after"
  fi
  count=$((count+1))
done < <(find "$TARGET_ROOT" -mindepth 2 -maxdepth 2 -type d -name "NT*_*" -print0)

echo "Done. processed=${count}"
