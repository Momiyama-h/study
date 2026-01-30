#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE_MINI="${BASE_MINI:-$REPO_ROOT/training}"
LOG_ROOT="${LOG_ROOT:-/HDD/momiyama2/data/study/training_logs}"
NTUPLE_DAT_ROOT="${NTUPLE_DAT_ROOT:-/HDD/momiyama2/data/study/ntuple_dat}"

RUN_TS="${RUN_TS:-$(date +%Y%m%d_%H%M)}"
RUN_NAME_BASE="${RUN_NAME_BASE:-trainonly_${RUN_TS}}"
SEEDS=(${SEEDS:-"5 6 7 8 9 10 11 12 13 14"})
STAGE_MODE="${STAGE_MODE:-stage}"
TUPLES_STR="${TUPLES:-4 6}"
PARALLEL="${PARALLEL:-8}"
STDOUT_LOG="${STDOUT_LOG:-0}"
INIT_EV="${INIT_EV:-}"
PARALLEL_BY_SEED=0

usage() {
  cat <<'USAGE'
Usage:
  run_train_only.sh [options]

Options:
  --run-name-base NAME   base run_name (default: trainonly_<ts>)
  --stage-mode MODE      stage|nostage|both (default: stage)
  --seed-start N         start seed (inclusive)
  --seed-end N           end seed (inclusive)
  --seeds "LIST"         explicit seed list (e.g. "5 6 7")
  --tuples "LIST"        tuple sizes (default: "4 6")
  --parallel N           max parallel jobs (default: 8)
  --parallel-by-seed     bundle sym/notsym per seed (only for 4/6)
  --stdout-log 0|1       enable stdout log in training (default: 0)
  --init-ev N            optimistic init value (INIT_EV)
  -h, --help             show help

Notes:
  - NT5a is supported only in stage or both. nostage-only with tuple 5 is not supported.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name-base) RUN_NAME_BASE="$2"; shift 2;;
    --stage-mode) STAGE_MODE="$2"; shift 2;;
    --seed-start) SEED_START="$2"; shift 2;;
    --seed-end) SEED_END="$2"; shift 2;;
    --seeds) read -r -a SEEDS <<< "$2"; shift 2;;
    --tuples) TUPLES_STR="$2"; shift 2;;
    --parallel) PARALLEL="$2"; shift 2;;
    --parallel-by-seed) PARALLEL_BY_SEED=1; shift;;
    --stdout-log) STDOUT_LOG="$2"; shift 2;;
    --init-ev) INIT_EV="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1" >&2; usage; exit 1;;
  esac
done

if [[ -n "${SEED_START:-}" || -n "${SEED_END:-}" ]]; then
  if [[ -z "${SEED_START:-}" || -z "${SEED_END:-}" ]]; then
    echo "ERROR: --seed-start and --seed-end must be used together" >&2
    exit 1
  fi
  SEEDS=()
  for ((s=SEED_START; s<=SEED_END; s++)); do SEEDS+=("$s"); done
fi

case "$STAGE_MODE" in
  stage|nostage|both) ;;
  *) echo "ERROR: invalid --stage-mode: $STAGE_MODE (use stage|nostage|both)" >&2; exit 1;;
 esac

TUPLES_STR="${TUPLES_STR//,/ }"
read -r -a TUPLES <<< "$TUPLES_STR"

has5=0
TUPLES_46=()
for t in "${TUPLES[@]}"; do
  case "$t" in
    4|6) TUPLES_46+=("$t");;
    5) has5=1;;
    *) echo "ERROR: unsupported tuple size: $t" >&2; exit 1;;
  esac
done

if [[ "$has5" -eq 1 && "$STAGE_MODE" == "nostage" ]]; then
  echo "ERROR: tuple 5 (NT5a) does not support nostage-only." >&2
  exit 1
fi

# Run NT4/NT6
if [[ ${#TUPLES_46[@]} -gt 0 ]]; then
  args=("--tuples" "${TUPLES_46[*]}")
  args+=("--stage-mode" "$STAGE_MODE")
  if [[ "$PARALLEL_BY_SEED" -eq 1 ]]; then
    args+=("--parallel-by-seed")
  fi
  SEEDS="${SEEDS[*]}"   RUN_NAME_BASE="$RUN_NAME_BASE"   PARALLEL="$PARALLEL"   STDOUT_LOG="$STDOUT_LOG"   INIT_EV="$INIT_EV"   LOG_ROOT="$LOG_ROOT"   NTUPLE_DAT_ROOT="$NTUPLE_DAT_ROOT"   "$SCRIPT_DIR/run_train_4patterns_10seeds_trainonly.sh" "${args[@]}"
fi

# Run NT5a
if [[ "$has5" -eq 1 ]]; then
  args=("--seeds" "${SEEDS[*]}" "--run-name-base" "$RUN_NAME_BASE" "--parallel" "$PARALLEL" "--stdout-log" "$STDOUT_LOG")
  if [[ -n "$INIT_EV" ]]; then
    args+=("--init-ev" "$INIT_EV")
  fi
  if [[ "$STAGE_MODE" == "both" ]]; then
    args+=("--nostage")
  fi
  LOG_ROOT="$LOG_ROOT" NTUPLE_DAT_ROOT="$NTUPLE_DAT_ROOT"     "$SCRIPT_DIR/run_train_nt5a_trainonly.sh" "${args[@]}"
fi
