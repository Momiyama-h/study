#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_train_rotate_compare.sh [options]

Purpose:
  Run paired training for 4-rotation symmetry vs no-symmetry:
  - rotate
  - rotate_notsym

Options:
  --run-name-base NAME   base run_name (default: rotatecmp_<ts>)
  --stage-mode MODE      stage|nostage|both (default: stage)
  --seed-start N         start seed (inclusive)
  --seed-end N           end seed (inclusive)
  --seeds "LIST"         explicit seeds (e.g. "7 8 9 10")
  --tuples "LIST"        tuple sizes (default: "4 5 6")
  --parallel N           max parallel jobs (default: 8)
  --stdout-log 0|1       training stdout toggle (default: 0)
  --policy MODE          greedy|expecti3 (default: greedy)
  --init-ev N            optimistic init value
  --nt4a                 use NT4a tuple set when tuple=4
  -h, --help             show help

Examples:
  ./run_train_rotate_compare.sh --run-name-base 20260220_OI1200 --seed-start 7 --seed-end 14
  ./run_train_rotate_compare.sh --run-name-base 20260220_OI1200 --seeds "7 8 9 10" --stage-mode both
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_TS="$(date +%Y%m%d_%H%M)"

RUN_NAME_BASE="rotatecmp_${RUN_TS}"
STAGE_MODE="stage"
SEED_START=""
SEED_END=""
SEEDS=""
TUPLES="4 5 6"
PARALLEL="8"
STDOUT_LOG="0"
POLICY="greedy"
INIT_EV=""
NT4A=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name-base) RUN_NAME_BASE="$2"; shift 2 ;;
    --stage-mode) STAGE_MODE="$2"; shift 2 ;;
    --seed-start) SEED_START="$2"; shift 2 ;;
    --seed-end) SEED_END="$2"; shift 2 ;;
    --seeds) SEEDS="$2"; shift 2 ;;
    --tuples) TUPLES="$2"; shift 2 ;;
    --parallel) PARALLEL="$2"; shift 2 ;;
    --stdout-log) STDOUT_LOG="$2"; shift 2 ;;
    --policy) POLICY="$2"; shift 2 ;;
    --init-ev) INIT_EV="$2"; shift 2 ;;
    --nt4a) NT4A=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -n "$SEEDS" && ( -n "$SEED_START" || -n "$SEED_END" ) ]]; then
  echo "ERROR: --seeds and --seed-start/--seed-end are mutually exclusive." >&2
  exit 1
fi

if [[ -z "$SEEDS" ]]; then
  if [[ -z "$SEED_START" || -z "$SEED_END" ]]; then
    echo "ERROR: provide --seeds or both --seed-start and --seed-end." >&2
    exit 1
  fi
fi

args=(
  --run-name-base "$RUN_NAME_BASE"
  --stage-mode "$STAGE_MODE"
  --tuples "$TUPLES"
  --modes "rotate rotate_notsym"
  --parallel "$PARALLEL"
  --stdout-log "$STDOUT_LOG"
  --policy "$POLICY"
)

if [[ -n "$SEEDS" ]]; then
  args+=(--seeds "$SEEDS")
else
  args+=(--seed-start "$SEED_START" --seed-end "$SEED_END")
fi

if [[ -n "$INIT_EV" ]]; then
  args+=(--init-ev "$INIT_EV")
fi

if [[ "$NT4A" -eq 1 ]]; then
  args+=(--nt4a)
fi

exec "$SCRIPT_DIR/run_train_unified.sh" "${args[@]}"

