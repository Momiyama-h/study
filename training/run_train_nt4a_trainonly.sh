#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE_MINI="${BASE_MINI:-$REPO_ROOT/training}"
LOG_ROOT="${LOG_ROOT:-/HDD/momiyama2/data/study/training_logs}"
NTUPLE_DAT_ROOT="${NTUPLE_DAT_ROOT:-/HDD/momiyama2/data/study/ntuple_dat}"

RUN_TS="${RUN_TS:-$(date +%Y%m%d_%H%M)}"
PARALLEL="${PARALLEL:-8}"
STDOUT_LOG="${STDOUT_LOG:-0}"
STAGE_MODES=(stage)
ALLOW_COLLIDE=0
RUN_NAME_SUFFIX=""
INIT_EV="${INIT_EV:-}"

SEEDS=(5 6 7 8 9 10 11 12 13 14)
SEED_SPEC="seed5-14"
RUN_NAME_BASE="trainonly_nt4a_${SEED_SPEC}_${RUN_TS}"

usage() {
  cat <<'USAGE'
Usage:
  run_train_nt4a_trainonly.sh [options]

Options:
  --run-name-base NAME   run_name base (default: trainonly_nt4a_seed5-14_<ts>)
  --run-name-suffix STR  suffix to avoid collisions (default: none)
  --allow-collide        allow overwriting existing NT4_sym/NT4_notsym under same run_name
  --seed N               run only a single seed
  --seed-start N         start seed (inclusive)
  --seed-end N           end seed (inclusive)
  --seeds "LIST"          explicit seed list (e.g. "5 6 7")
  --stage-only           stage only (default)
  --nostage              also run nostage (SINGLE_STAGE)
  --parallel N           max parallel jobs (default: 8)
  --stdout-log 0|1       enable stdout log in training (default: 0)
  --init-ev N            optimistic init value (INIT_EV) for learning
  -h, --help             show help

Env (optional):
  BASE_MINI, LOG_ROOT, NTUPLE_DAT_ROOT, RUN_TS, PARALLEL, STDOUT_LOG, INIT_EV
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name-base) RUN_NAME_BASE="$2"; shift 2;;
    --run-name-suffix) RUN_NAME_SUFFIX="$2"; shift 2;;
    --allow-collide) ALLOW_COLLIDE=1; shift;;
    --seed) SEEDS=("$2"); SEED_SPEC="seed$2"; shift 2;;
    --seed-start) SEED_START="$2"; shift 2;;
    --seed-end) SEED_END="$2"; shift 2;;
    --seeds) read -r -a SEEDS <<< "$2"; SEED_SPEC="seed${SEEDS[0]}-${SEEDS[-1]}"; shift 2;;
    --stage-only) STAGE_MODES=(stage); shift;;
    --nostage) STAGE_MODES=(stage nostage); shift;;
    --parallel) PARALLEL="$2"; shift 2;;
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
  SEED_SPEC="seed${SEED_START}-${SEED_END}"
fi

RUN_NAME_BASE="${RUN_NAME_BASE/${SEED_SPEC}/${SEED_SPEC}}"
if [[ -n "$RUN_NAME_SUFFIX" ]]; then
  RUN_NAME_BASE+="$RUN_NAME_SUFFIX"
fi

compile_train() {
  local src="$1"
  local out="$2"
  local extra="${3:-}"
  echo "Compile: $src -> $out $extra"
  g++ "$src" -O3 -std=c++20 $extra -o "$out"
}

run_one() {
  local symmetry="$1"
  local train_bin="$2"
  local seed="$3"
  local stage_tag="$4"
  local run_name="$5"

  local dat_dir="${NTUPLE_DAT_ROOT}/${run_name}/seed${seed}/NT4_${symmetry}"
  local log_dir="${LOG_ROOT}/${run_name}/seed${seed}/NT4_${symmetry}"
  mkdir -p "$dat_dir" "$log_dir"
  local log_file="${log_dir}/log_4tuple_${symmetry}_seed${seed}_${RUN_TS}__${stage_tag}.txt"
  echo "== Train: 4${symmetry} seed=${seed} stage=${stage_tag} ==" | tee "$log_file"
  ( INIT_EV="$INIT_EV" NTUPLE_DAT_ROOT="$NTUPLE_DAT_ROOT" CSV_LOG_TAG="$stage_tag" "$train_bin" "$seed" "$run_name" ) \
    2>&1 | tee -a "$log_file"
  echo | tee -a "$log_file"
}

check_collide() {
  local run_name="$1"
  for seed in "${SEEDS[@]}"; do
    if [[ -d "${NTUPLE_DAT_ROOT}/${run_name}/seed${seed}/NT4_sym" || -d "${NTUPLE_DAT_ROOT}/${run_name}/seed${seed}/NT4_notsym" ]]; then
      return 0
    fi
  done
  return 1
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
  if [[ "$ALLOW_COLLIDE" -eq 0 ]]; then
    if check_collide "$run_name"; then
      if [[ "$RUN_NAME_BASE" != *"__nt4a" ]]; then
        echo "WARN: run_name collision detected for $run_name. Appending __nt4a to base." >&2
        RUN_NAME_BASE+="__nt4a"
        run_name="${RUN_NAME_BASE}__${stage_tag}"
      fi
    fi
  fi

  compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_4asym${bin_suffix}" "-DUSE_4TUPLE -DNT4A $train_flags"
  compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_4anotsym${bin_suffix}" "-DUSE_4TUPLE -DNT4A $train_flags"

  JOBS=0
  for seed in "${SEEDS[@]}"; do
    run_one sym "$BASE_MINI/learn_4asym${bin_suffix}" "$seed" "$stage_tag" "$run_name" &
    JOBS=$((JOBS+1))
    if [ "$JOBS" -ge "$PARALLEL" ]; then
      wait -n
      JOBS=$((JOBS-1))
    fi
    run_one notsym "$BASE_MINI/learn_4anotsym${bin_suffix}" "$seed" "$stage_tag" "$run_name" &
    JOBS=$((JOBS+1))
    if [ "$JOBS" -ge "$PARALLEL" ]; then
      wait -n
      JOBS=$((JOBS-1))
    fi
  done
  wait
  echo "== Completed stage_mode=${stage_tag} =="
  echo

done
