#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE_MINI="${BASE_MINI:-$REPO_ROOT/training}"
LOG_ROOT="${LOG_ROOT:-/HDD/momiyama2/data/study/training_logs}"
NTUPLE_DAT_ROOT="${NTUPLE_DAT_ROOT:-/HDD/momiyama2/data/study/ntuple_dat}"

SEEDS=(${SEEDS:-"5 6 7 8 9 10 11 12 13 14"})
RUN_TS="${RUN_TS:-$(date +%Y%m%d_%H%M)}"
PARALLEL="${PARALLEL:-8}"
STDOUT_LOG="${STDOUT_LOG:-0}"
RUN_NAME_BASE="${RUN_NAME_BASE:-trainonly_${RUN_TS}}"
STAGE_MODE="${STAGE_MODE:-}"
STAGE_MODES_STR="${STAGE_MODES:-nostage stage}"
NTUPLES_STR="${NTUPLES:-4 6}"
PARALLEL_BY_SEED=0

usage() {
  cat <<'USAGE'
Usage:
  run_train_4patterns_10seeds_trainonly.sh [options]

Options:
  --sequential            run sequentially (PARALLEL=1)
  --parallel-by-seed      run 4 patterns per seed as a bundle
  --stage-only            run stage only
  --nostage               run nostage only
  --stage-mode MODE       stage|nostage|both (overrides STAGE_MODES/STAGE_MODE)
  --stage-modes LIST      comma/space list (e.g. "stage,nostage")
  --tuples LIST           comma/space list (default: "4 6")
  -h, --help              show help

Env (optional):
  SEEDS, RUN_TS, PARALLEL, STDOUT_LOG, RUN_NAME_BASE,
  STAGE_MODE, STAGE_MODES, NTUPLES, BASE_MINI, LOG_ROOT, NTUPLE_DAT_ROOT
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sequential) PARALLEL=1; shift;;
    --parallel-by-seed) PARALLEL_BY_SEED=1; shift;;
    --stage-only) STAGE_MODE="stage"; shift;;
    --nostage) STAGE_MODE="nostage"; shift;;
    --stage-mode) STAGE_MODE="$2"; shift 2;;
    --stage-modes) STAGE_MODES_STR="$2"; shift 2;;
    --tuples) NTUPLES_STR="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1" >&2; usage; exit 1;;
  esac
done

if [[ -n "$STAGE_MODE" ]]; then
  case "$STAGE_MODE" in
    stage) STAGE_MODES_STR="stage" ;;
    nostage) STAGE_MODES_STR="nostage" ;;
    both|all) STAGE_MODES_STR="nostage stage" ;;
    *)
      echo "ERROR: invalid STAGE_MODE: $STAGE_MODE (use stage|nostage|both)" >&2
      exit 1
      ;;
  esac
fi

STAGE_MODES_STR="${STAGE_MODES_STR//,/ }"
read -r -a STAGE_MODES <<< "$STAGE_MODES_STR"
NTUPLES_STR="${NTUPLES_STR//,/ }"
read -r -a NTUPLES <<< "$NTUPLES_STR"

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
  ( NTUPLE_DAT_ROOT="$NTUPLE_DAT_ROOT" CSV_LOG_TAG="$stage_tag" "$train_bin" "$seed" "$run_name" ) \
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

run_seed_bundle() {
  local seed="$1"
  local stage_tag="$2"
  local run_name="$3"
  local bin_suffix="$4"
  for tuple in "${NTUPLES[@]}"; do
    run_one "$tuple" sym "$BASE_MINI/learn_${tuple}sym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
    run_one "$tuple" notsym "$BASE_MINI/learn_${tuple}notsym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
  done
}

for stage_mode in "${STAGE_MODES[@]}"; do
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

  for tuple in "${NTUPLES[@]}"; do
    case "$tuple" in
      4)
        compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_4sym${bin_suffix}" "-DUSE_4TUPLE $train_flags"
        compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_4notsym${bin_suffix}" "-DUSE_4TUPLE $train_flags"
        ;;
      6)
        compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_6sym${bin_suffix}" "$train_flags"
        compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_6notsym${bin_suffix}" "$train_flags"
        ;;
      *)
        echo "ERROR: unsupported tuple size: $tuple (use 4 or 6)" >&2
        exit 1
        ;;
    esac
  done

  JOBS=0
  if [[ "$PARALLEL_BY_SEED" -eq 1 ]]; then
    for seed in "${SEEDS[@]}"; do
      run_seed_bundle "$seed" "$stage_tag" "$run_name" "$bin_suffix" &
      JOBS=$((JOBS+1))
      if [ "$JOBS" -ge "$PARALLEL" ]; then
        wait -n
        JOBS=$((JOBS-1))
      fi
    done
  else
    for seed in "${SEEDS[@]}"; do
      for tuple in "${NTUPLES[@]}"; do
        spawn_job "$tuple" sym "$BASE_MINI/learn_${tuple}sym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
        spawn_job "$tuple" notsym "$BASE_MINI/learn_${tuple}notsym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
      done
    done
  fi
  wait
  echo "== Completed stage_mode=${stage_tag} =="
  echo
done
