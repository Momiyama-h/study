#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_eval_scores_from_dat.sh --run-name NAME [options]

Options:
  --run-name NAME        run_name under ntuple_dat (required)
  --seed-start N         start seed (optional)
  --seed-end N           end seed (optional)
  --seeds "LIST"         explicit seed list (e.g. "5 6 7") (optional)
  --stage N              stage suffix for dat filename (default: 9)
  --tuples LIST          comma-separated tuples (default: 4,6)
  --sym-list LIST        comma-separated sym list (default: sym,notsym)
  --games N              number of games (default: 10000)
  --avescope N           averaging window (default: 1000)
  --parallel N           parallel jobs (default: 1)
  --nostage              force SINGLE_STAGE build (stage0 only)
  --dat-root PATH        base of ntuple_dat (default: /HDD/momiyama2/data/study/ntuple_dat)
  --output-root PATH     base of output CSV (default: /HDD/momiyama2/data/study/analysis_outputs/training_scores_from_dat)
USAGE
}

RUN_NAME=""
SEED_START=""
SEED_END=""
SEEDS=""
STAGE=9
TUPLES="4,6"
SYM_LIST="sym,notsym"
GAMES=10000
AVESCOPE=1000
PARALLEL=1
SINGLE_STAGE=0

DAT_ROOT="/HDD/momiyama2/data/study/ntuple_dat"
OUT_ROOT="/HDD/momiyama2/data/study/analysis_outputs/training_scores_from_dat"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name) RUN_NAME="$2"; shift 2;;
    --seed-start) SEED_START="$2"; shift 2;;
    --seed-end) SEED_END="$2"; shift 2;;
    --seeds) SEEDS="$2"; shift 2;;
    --stage) STAGE="$2"; shift 2;;
    --tuples) TUPLES="$2"; shift 2;;
    --sym-list) SYM_LIST="$2"; shift 2;;
    --games) GAMES="$2"; shift 2;;
    --avescope) AVESCOPE="$2"; shift 2;;
    --parallel) PARALLEL="$2"; shift 2;;
    --nostage) SINGLE_STAGE=1; shift;;
    --dat-root) DAT_ROOT="$2"; shift 2;;
    --output-root) OUT_ROOT="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1"; usage; exit 1;;
  esac
done

if [[ -z "$RUN_NAME" ]]; then
  echo "ERROR: --run-name is required." >&2
  exit 1
fi

if [[ -n "$SEEDS" ]]; then
  read -r -a SEED_ARR <<< "$SEEDS"
elif [[ -n "$SEED_START" && -n "$SEED_END" ]]; then
  SEED_ARR=()
  for ((s=SEED_START; s<=SEED_END; s++)); do
    SEED_ARR+=("$s")
  done
else
  echo "ERROR: --seed-start/--seed-end or --seeds is required." >&2
  exit 1
fi

IFS=',' read -r -a TUPLE_ARR <<< "$TUPLES"
IFS=',' read -r -a SYM_ARR <<< "$SYM_LIST"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${SCRIPT_DIR}/eval_scores_from_dat.cpp"
BIN_DIR="${SCRIPT_DIR}/bin"
mkdir -p "$BIN_DIR"

compile_bin() {
  local bin="$1"
  shift
  local flags=("$@")
  if [[ ! -x "$bin" || "$SRC" -nt "$bin" ]]; then
    echo "Compile: $SRC -> $bin ${flags[*]}"
    g++ -O3 -std=c++17 "$SRC" "${flags[@]}" -o "$bin"
  fi
}

COMMON_FLAGS=()
if [[ "$SINGLE_STAGE" -eq 1 ]]; then
  COMMON_FLAGS+=("-DSINGLE_STAGE")
fi

compile_bin "${BIN_DIR}/eval_scores_nt4_sym" -DUSE_4TUPLE "${COMMON_FLAGS[@]}"
compile_bin "${BIN_DIR}/eval_scores_nt4_notsym" -DUSE_4TUPLE -DUSE_NOSYM "${COMMON_FLAGS[@]}"
compile_bin "${BIN_DIR}/eval_scores_nt6_sym" "${COMMON_FLAGS[@]}"
compile_bin "${BIN_DIR}/eval_scores_nt6_notsym" -DUSE_NOSYM "${COMMON_FLAGS[@]}"

run_one() {
  local seed="$1"
  local tuple="$2"
  local sym="$3"

  local tuple_prefix
  tuple_prefix="${tuple}tuple"

  local bin=""
  if [[ "$tuple" -eq 4 && "$sym" == "sym" ]]; then
    bin="${BIN_DIR}/eval_scores_nt4_sym"
  elif [[ "$tuple" -eq 4 && "$sym" == "notsym" ]]; then
    bin="${BIN_DIR}/eval_scores_nt4_notsym"
  elif [[ "$tuple" -eq 6 && "$sym" == "sym" ]]; then
    bin="${BIN_DIR}/eval_scores_nt6_sym"
  else
    bin="${BIN_DIR}/eval_scores_nt6_notsym"
  fi

  local dat_dir="${DAT_ROOT}/${RUN_NAME}/seed${seed}/NT${tuple}_${sym}"
  local dat_file="${tuple_prefix}_${sym}_data_${seed}_${STAGE}.dat"
  local dat_path="${dat_dir}/${dat_file}"
  if [[ ! -f "$dat_path" ]]; then
    echo "MISSING: $dat_path" >&2
    return 0
  fi

  local out_dir="${OUT_ROOT}/${RUN_NAME}/NT${tuple}/${sym}"
  mkdir -p "$out_dir"
  local out_csv="${out_dir}/score_seed${seed}_NT${tuple}_${sym}_stage${STAGE}.csv"

  "$bin" "$dat_path" "$out_csv" --games "$GAMES" --avescope "$AVESCOPE" --seed "$seed"
  echo "wrote: $out_csv"
}

running=0
for seed in "${SEED_ARR[@]}"; do
  for tuple in "${TUPLE_ARR[@]}"; do
    for sym in "${SYM_ARR[@]}"; do
      run_one "$seed" "$tuple" "$sym" &
      running=$((running + 1))
      if [[ "$PARALLEL" -gt 0 && "$running" -ge "$PARALLEL" ]]; then
        wait -n
        running=$((running - 1))
      fi
    done
  done
done
wait
