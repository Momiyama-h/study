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
TUPLES_STR="${TUPLES:-4 5 6}"
PARALLEL="${PARALLEL:-8}"
STDOUT_LOG="${STDOUT_LOG:-0}"
INIT_EV="${INIT_EV:-}"
NT4A="${NT4A:-0}"

usage() {
  cat <<'USAGE'
Usage:
  run_train_unified.sh [options]

Options:
  --run-name-base NAME   base run_name (default: trainonly_<ts>)
  --stage-mode MODE      stage|nostage|both (default: stage)
  --seed-start N         start seed (inclusive)
  --seed-end N           end seed (inclusive)
  --seeds "LIST"         explicit seed list (e.g. "5 6 7")
  --tuples "LIST"        tuple sizes (default: "4 5 6")
  --parallel N           max parallel jobs (default: 8)
  --stdout-log 0|1       enable stdout log in training (default: 0)
  --init-ev N            optimistic init value (INIT_EV)
  --nt4a                 use NT4a tuple set when tuple=4
  -h, --help             show help

Outputs:
  - .dat: ${NTUPLE_DAT_ROOT}/<run_name>/seed<seed>/NT{4|5|6}_{sym|notsym}/
  - log: ${LOG_ROOT}/<run_name>/seed<seed>/NT{4|5|6}_{sym|notsym}/
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
    --stdout-log) STDOUT_LOG="$2"; shift 2;;
    --init-ev) INIT_EV="$2"; shift 2;;
    --nt4a) NT4A=1; shift;;
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

if [[ "$NT4A" -eq 1 ]]; then
  for t in "${TUPLES[@]}"; do
    if [[ "$t" == "4" ]]; then
      if [[ "$RUN_NAME_BASE" != *"__nt4a"* ]]; then
        RUN_NAME_BASE="${RUN_NAME_BASE}__nt4a"
      fi
      break
    fi
  done
fi

compile_train() {
  local src="$1"
  local out="$2"
  local extra="${3:-}"
  echo "Compile: $src -> $out $extra"
  g++ "$src" -O3 -std=c++20 $extra -o "$out"
}

run_one() {
  local tuple="$1"
  local symmetry="$2"
  local train_bin="$3"
  local seed="$4"
  local stage_tag="$5"
  local run_name="$6"

  local dat_dir="${NTUPLE_DAT_ROOT}/${run_name}/seed${seed}/NT${tuple}_${symmetry}"
  local log_dir="${LOG_ROOT}/${run_name}/seed${seed}/NT${tuple}_${symmetry}"
  mkdir -p "$dat_dir" "$log_dir"
  local log_file="${log_dir}/log_${tuple}tuple_${symmetry}_seed${seed}_${RUN_TS}__${stage_tag}.txt"
  echo "== Train: ${tuple}${symmetry} seed=${seed} stage=${stage_tag} ==" | tee "$log_file"
  ( INIT_EV="$INIT_EV" NTUPLE_DAT_ROOT="$NTUPLE_DAT_ROOT" CSV_LOG_TAG="$stage_tag" "$train_bin" "$seed" "$run_name" ) \
    2>&1 | tee -a "$log_file"
  echo | tee -a "$log_file"
}

spawn_job() {
  run_one "$@" &
  JOBS=$((JOBS+1))
  if [ "$JOBS" -ge "$PARALLEL" ]; then
    wait -n
    JOBS=$((JOBS-1))
  fi
}

for stage_mode in $(echo "$STAGE_MODE" | sed 's/both/stage nostage/'); do
  case "$stage_mode" in
    stage)
      stage_tag="stage"
      train_flags="-DENABLE_CSV_LOG=1 -DENABLE_STDOUT_LOG=${STDOUT_LOG}"
      bin_suffix="_st"
      ;;
    nostage)
      stage_tag="nostage"
      train_flags="-DSINGLE_STAGE -DENABLE_CSV_LOG=1 -DENABLE_STDOUT_LOG=${STDOUT_LOG}"
      bin_suffix="_ns"
      ;;
    *)
      echo "ERROR: Unknown stage_mode: $stage_mode" >&2
      exit 1
      ;;
  esac

  run_name="${RUN_NAME_BASE}__${stage_tag}"

  # compile required tuples for this stage mode
  for tuple in "${TUPLES[@]}"; do
    case "$tuple" in
      4)
        if [[ "$NT4A" -eq 1 ]]; then
          compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_4sym${bin_suffix}" "-DUSE_4TUPLE -DNT4A $train_flags"
          compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_4notsym${bin_suffix}" "-DUSE_4TUPLE -DNT4A $train_flags"
        else
          compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_4sym${bin_suffix}" "-DUSE_4TUPLE $train_flags"
          compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_4notsym${bin_suffix}" "-DUSE_4TUPLE $train_flags"
        fi
        ;;
      5)
        compile_train "$BASE_MINI/learning_ntuple_sym_nt5a.cpp" "$BASE_MINI/learn_5sym${bin_suffix}" "-DUSE_5TUPLE $train_flags"
        compile_train "$BASE_MINI/learning_ntuple_notsym_nt5a.cpp" "$BASE_MINI/learn_5notsym${bin_suffix}" "-DUSE_5TUPLE $train_flags"
        ;;
      6)
        compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_6sym${bin_suffix}" "$train_flags"
        compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_6notsym${bin_suffix}" "$train_flags"
        ;;
      *)
        echo "ERROR: unsupported tuple size: $tuple" >&2
        exit 1
        ;;
    esac
  done

  JOBS=0
  for seed in "${SEEDS[@]}"; do
    for tuple in "${TUPLES[@]}"; do
      case "$tuple" in
        4)
          spawn_job 4 sym "$BASE_MINI/learn_4sym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
          spawn_job 4 notsym "$BASE_MINI/learn_4notsym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
          ;;
        5)
          spawn_job 5 sym "$BASE_MINI/learn_5sym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
          spawn_job 5 notsym "$BASE_MINI/learn_5notsym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
          ;;
        6)
          spawn_job 6 sym "$BASE_MINI/learn_6sym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
          spawn_job 6 notsym "$BASE_MINI/learn_6notsym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
          ;;
      esac
    done
  done
  wait
  echo "== Completed stage_mode=${stage_tag} =="
  echo

done
