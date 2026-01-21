#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE_MINI="${BASE_MINI:-$REPO_ROOT/training}"
BASE_NT="${BASE_NT:-$REPO_ROOT/Mini-2048-data-processing-main/NT}"
LOG_ROOT="${LOG_ROOT:-/HDD/momiyama2/data/study/training_logs}"
BOARD_DATA_PARENT="${BOARD_DATA_PARENT:-${BASE_NT}/../board_data}"

SEEDS=(${SEEDS:-"15 16 17 18 19 20 21 22 23 24"})
SEED_SPEC="${SEED_SPEC:-seed15-24}"
GAME_COUNT=100
RUN_TS="${RUN_TS:-$(date +%Y%m%d_%H%M)}"
PARALLEL="${PARALLEL:-8}"
STDOUT_LOG="${STDOUT_LOG:-0}"
EV_STAGE="${EV_STAGE:-9}"
STAGE_MODES=(${STAGE_MODES:-"stage nostage"})

DAT_ROOT_BASE="${DAT_ROOT_BASE:-/HDD/momiyama2/data/study/ntuple_dat/stage_compare/${SEED_SPEC}/g${GAME_COUNT}/${RUN_TS}}"

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
  local prefix="$4"
  local seed="$5"
  local stage_tag="$6"
  local play_bin="$7"
  local dat_root="$8"

  mkdir -p "$dat_root" "$LOG_ROOT"
  local log_file="${LOG_ROOT}/log_${tuple}tuple_${symmetry}_seed${seed}_${RUN_TS}__${stage_tag}.txt"
  echo "== Train: ${tuple}${symmetry} seed=${seed} stage=${stage_tag} ==" | tee "$log_file"
  ( cd "$dat_root" && CSV_LOG_TAG="$stage_tag" "$train_bin" "$seed" ) 2>&1 | tee -a "$log_file"
  local evfile="${dat_root}/${prefix}_${seed}_${EV_STAGE}.dat"
  if [ ! -f "$evfile" ]; then
    echo "ERROR: evfile not found: $evfile" | tee -a "$log_file" >&2
    exit 1
  fi
  local root="${BOARD_DATA_PARENT}/${RUN_TS}_${tuple}${symmetry}_seed${seed}_g${GAME_COUNT}__${stage_tag}"
  echo "== Eval: BOARD_DATA_ROOT=${root} ==" | tee -a "$log_file"
  BOARD_DATA_ROOT="$root" "$play_bin" "$seed" "$GAME_COUNT" "$evfile" "$symmetry" "$tuple" \
    2>&1 | tee -a "$log_file"

  local data_dir="${root}/NT${tuple}_${symmetry}"
  local meta_path="${data_dir}/meta.json"
  local write_meta="${REPO_ROOT}/Mini-2048-data-processing-main/write_meta.py"
  if [ -f "$write_meta" ] && [ -d "$data_dir" ]; then
    if [ -f "$meta_path" ]; then
      echo "== Meta: skip (exists) ${meta_path} ==" | tee -a "$log_file"
    else
      echo "== Meta: create ${meta_path} ==" | tee -a "$log_file"
      python3 "$write_meta" --board-dir "$BOARD_DATA_PARENT" "$data_dir" "$evfile" \
        2>&1 | tee -a "$log_file"
    fi
  else
    echo "WARN: meta.json skipped (missing write_meta.py or data_dir)" | tee -a "$log_file"
  fi
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
      play_flags=""
      bin_suffix="_st"
      ;;
    nostage)
      stage_tag="nostage"
      train_flags="-DSINGLE_STAGE -DENABLE_CSV_LOG=1 -DENABLE_STDOUT_LOG=${STDOUT_LOG}"
      play_flags="-DSINGLE_STAGE"
      bin_suffix="_ns"
      ;;
    *)
      echo "ERROR: Unknown stage_mode: $stage_mode" >&2
      exit 1
      ;;
  esac

  dat_root="${DAT_ROOT_BASE}/${stage_tag}"

  compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_6sym${bin_suffix}" "$train_flags"
  compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_6notsym${bin_suffix}" "$train_flags"
  compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_4sym${bin_suffix}" "-DUSE_4TUPLE $train_flags"
  compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_4notsym${bin_suffix}" "-DUSE_4TUPLE $train_flags"

  echo "Compile: Play_NT_player.cpp -> play_nt${bin_suffix}"
  g++ "$BASE_NT/Play_NT_player.cpp" -O2 -std=c++20 $play_flags -o "$BASE_NT/play_nt${bin_suffix}"
  echo

  JOBS=0
  for seed in "${SEEDS[@]}"; do
    spawn_job 4 sym "$BASE_MINI/learn_4sym${bin_suffix}" "4tuple_sym_data" "$seed" "$stage_tag" "$BASE_NT/play_nt${bin_suffix}" "$dat_root"
    spawn_job 4 notsym "$BASE_MINI/learn_4notsym${bin_suffix}" "4tuple_notsym_data" "$seed" "$stage_tag" "$BASE_NT/play_nt${bin_suffix}" "$dat_root"
    spawn_job 6 sym "$BASE_MINI/learn_6sym${bin_suffix}" "6tuple_sym_data" "$seed" "$stage_tag" "$BASE_NT/play_nt${bin_suffix}" "$dat_root"
    spawn_job 6 notsym "$BASE_MINI/learn_6notsym${bin_suffix}" "6tuple_notsym_data" "$seed" "$stage_tag" "$BASE_NT/play_nt${bin_suffix}" "$dat_root"
  done
  wait
  echo "== Completed stage_mode=${stage_tag} =="
  echo

done
