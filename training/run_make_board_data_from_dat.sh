#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_make_board_data_from_dat.sh --run-name NAME --seed-start N --seed-end N --ev-stages LIST

Options:
  --run-name NAME    run_name (required)
  --seed-start N     start seed (required)
  --seed-end N       end seed (required)
  --ev-stages LIST   comma-separated stage list (e.g. 0,1,2 or 9) (required)
  --tuples LIST      comma-separated tuples (default: 4,6)
  --sym-list LIST    comma-separated sym list (default: sym,notsym)
  --game-count N     game count per eval (default: 10000)
  --parallel N       max parallel jobs (default: nproc)
  --board-root PATH  board_data root (default: /HDD/momiyama2/data/study/board_data)
  --dat-root PATH    ntuple_dat root (default: /HDD/momiyama2/data/study/ntuple_dat)
USAGE
}

RUN_NAME=""
SEED_START=""
SEED_END=""
EV_STAGES=""
TUPLES="4,6"
SYM_LIST="sym,notsym"
GAME_COUNT=10000
PARALLEL="$(nproc)"
BOARD_ROOT="/HDD/momiyama2/data/study/board_data"
DAT_ROOT="/HDD/momiyama2/data/study/ntuple_dat"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name) RUN_NAME="$2"; shift 2;;
    --seed-start) SEED_START="$2"; shift 2;;
    --seed-end) SEED_END="$2"; shift 2;;
    --ev-stages) EV_STAGES="$2"; shift 2;;
    --tuples) TUPLES="$2"; shift 2;;
    --sym-list) SYM_LIST="$2"; shift 2;;
    --game-count) GAME_COUNT="$2"; shift 2;;
    --parallel) PARALLEL="$2"; shift 2;;
    --board-root) BOARD_ROOT="$2"; shift 2;;
    --dat-root) DAT_ROOT="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1"; usage; exit 1;;
  esac
done

if [[ -z "$RUN_NAME" || -z "$SEED_START" || -z "$SEED_END" || -z "$EV_STAGES" ]]; then
  echo "ERROR: --run-name/--seed-start/--seed-end/--ev-stages are required." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE_NT="${BASE_NT:-$REPO_ROOT/Mini-2048-data-processing-main/NT}"

if [ ! -x "$BASE_NT/play_nt" ]; then
  ( cd "$BASE_NT" && g++ Play_NT_player.cpp -O2 -std=c++20 -o play_nt )
fi

IFS=',' read -r -a TUPLE_ARR <<< "$TUPLES"
IFS=',' read -r -a SYM_ARR <<< "$SYM_LIST"
IFS=',' read -r -a STAGE_ARR <<< "$EV_STAGES"

run_one() {
  local seed="$1"
  local tuple="$2"
  local sym="$3"
  local stage="$4"

  local dat_dir="${DAT_ROOT}/${RUN_NAME}/seed${seed}/NT${tuple}_${sym}"
  local evfile="${dat_dir}/${tuple}tuple_${sym}_data_${seed}_${stage}.dat"
  if [ ! -f "$evfile" ]; then
    echo "MISSING: $evfile" >&2
    return 1
  fi
  "$BASE_NT/play_nt" "$seed" "$GAME_COUNT" "$evfile" "$sym" "$tuple" \
    --run-name "$RUN_NAME" --board-root "$BOARD_ROOT"

  local data_dir="${BOARD_ROOT}/${RUN_NAME}/seed${seed}/NT${tuple}_${sym}"
  local write_meta="${REPO_ROOT}/Mini-2048-data-processing-main/write_meta.py"
  if [ -f "$write_meta" ] && [ -d "$data_dir" ]; then
    local meta_path="${data_dir}/meta.json"
    if [ ! -f "$meta_path" ]; then
      python3 "$write_meta" --board-dir "$BOARD_ROOT" "$data_dir" "$evfile"
    fi
  fi
}

spawn_job() {
  run_one "$@" &
  JOBS=$((JOBS+1))
  if [ "$JOBS" -ge "$PARALLEL" ]; then
    wait -n
    JOBS=$((JOBS-1))
  fi
}

JOBS=0
for seed in $(seq "$SEED_START" "$SEED_END"); do
  for tuple in "${TUPLE_ARR[@]}"; do
    for sym in "${SYM_ARR[@]}"; do
      for stage in "${STAGE_ARR[@]}"; do
        spawn_job "$seed" "$tuple" "$sym" "$stage"
      done
    done
  done
done
wait
