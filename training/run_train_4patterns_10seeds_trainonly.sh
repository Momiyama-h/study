#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE_MINI="${BASE_MINI:-$REPO_ROOT/training}"
LOG_ROOT="${LOG_ROOT:-/HDD/momiyama2/data/study/training_logs}"
NTUPLE_DAT_ROOT="${NTUPLE_DAT_ROOT:-/HDD/momiyama2/data/study/ntuple_dat}"

SEEDS=(${SEEDS:-"5 6 7 8 9 10 11 12 13 14"})
SEED_SPEC="${SEED_SPEC:-seed5-14}"
RUN_TS="${RUN_TS:-$(date +%Y%m%d_%H%M)}"
PARALLEL="${PARALLEL:-$(nproc)}"
STDOUT_LOG="${STDOUT_LOG:-0}"
RUN_NAME_BASE="${RUN_NAME_BASE:-trainonly_${SEED_SPEC}_${RUN_TS}}"
STAGE_MODES_STR="${STAGE_MODES:-nostage stage}"
STAGE_MODES_STR="${STAGE_MODES_STR//,/ }"
read -r -a STAGE_MODES <<< "$STAGE_MODES_STR"

compile_train() {
  local src="$1"
  local out="$2"
  local extra="${3:-}"
  echo "Compile: $src -> $out $extra"
  g++ "$src" -O2 -std=c++20 $extra -o "$out"
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

  compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_6sym${bin_suffix}" "$train_flags"
  compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_6notsym${bin_suffix}" "$train_flags"
  compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_4sym${bin_suffix}" "-DUSE_4TUPLE $train_flags"
  compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_4notsym${bin_suffix}" "-DUSE_4TUPLE $train_flags"

  JOBS=0
  for seed in "${SEEDS[@]}"; do
    spawn_job 4 sym "$BASE_MINI/learn_4sym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
    spawn_job 4 notsym "$BASE_MINI/learn_4notsym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
    spawn_job 6 sym "$BASE_MINI/learn_6sym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
    spawn_job 6 notsym "$BASE_MINI/learn_6notsym${bin_suffix}" "$seed" "$stage_tag" "$run_name"
  done
  wait
  echo "== Completed stage_mode=${stage_tag} =="
  echo
done
