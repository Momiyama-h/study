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
  --parallel N        max parallel jobs (default: nproc)
  -h, --help          show this help
USAGE
}

RUN_NAME=""
BOARD_ROOT=""
OUTPUT_MODE="per-nt"
FORCE=0
PARALLEL="$(nproc)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name) RUN_NAME="$2"; shift 2;;
    --board-root) BOARD_ROOT="$2"; shift 2;;
    --output-mode) OUTPUT_MODE="$2"; shift 2;;
    --force) FORCE=1; shift;;
    --parallel) PARALLEL="$2"; shift 2;;
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
BOARD_ROOT_REAL="$(readlink -f "$BOARD_ROOT")"

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
JOBS=0

run_one() {
  local d="$1"
  d_real="$(readlink -f "$d")"
  case "$d_real" in
    "$BOARD_ROOT_REAL"/*) ;;
    *)
      echo "WARN: skip (outside board_root): $d_real" >&2
      return 0
      ;;
  esac
  rel="${d_real#$BOARD_ROOT_REAL/}"
  safe="${rel//\//__}"
  safe="${safe//\\/__}"
  out_state="$BOARD_ROOT/PP/eval-state-${safe}.txt"
  out_after="$BOARD_ROOT/PP/eval-after-state-${safe}.txt"
  local_state="$d/eval-state.txt"
  local_after="$d/eval-after-state.txt"

  if [ "$OUTPUT_MODE" = "per-nt" ]; then
    if [ "$FORCE" -eq 0 ] && [ -f "$local_state" ] && [ -f "$local_after" ]; then
      return 0
    fi
  else
    if [ "$FORCE" -eq 0 ] && [ -f "$out_state" ] && [ -f "$out_after" ]; then
      return 0
    fi
  fi

  if ! state_report="$(cd "$SCRIPT_DIR" && ./eval_state_pp "$rel")"; then
    echo "ERROR: eval_state_pp failed for $rel" >&2
    return 1
  fi
  if ! after_report="$(cd "$SCRIPT_DIR" && ./eval_after_state_pp "$rel")"; then
    echo "ERROR: eval_after_state_pp failed for $rel" >&2
    return 1
  fi

  state_path="$(printf "%s\n" "$state_report" | awk '/Results saved to/{print $NF}' | tail -n1)"
  after_path="$(printf "%s\n" "$after_report" | awk '/Results saved to/{print $NF}' | tail -n1)"
  [ -n "$state_path" ] || state_path="$out_state"
  [ -n "$after_path" ] || after_path="$out_after"

  if [ "$OUTPUT_MODE" = "per-nt" ]; then
    mv -f "$state_path" "$local_state"
    mv -f "$after_path" "$local_after"
  fi
  count=$((count+1))
}

spawn_job() {
  run_one "$1" &
  JOBS=$((JOBS+1))
  if [ "$JOBS" -ge "$PARALLEL" ]; then
    wait -n
    JOBS=$((JOBS-1))
  fi
}

while IFS= read -r -d '' d; do
  spawn_job "$d"
done < <(find "$TARGET_ROOT" -mindepth 2 -maxdepth 2 -type d -name "NT*_*" -print0)
wait

echo "Done. processed=${count}"
