#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE_MINI="${BASE_MINI:-$REPO_ROOT/training}"
BASE_NT="${BASE_NT:-$REPO_ROOT/Mini-2048-data-processing-main/NT}"
LOG_ROOT="${LOG_ROOT:-/HDD/momiyama2/data/study/training_logs}"
BOARD_DATA_PARENT="${BOARD_DATA_PARENT:-${BASE_NT}/../board_data}"

SEEDS=(5 6 7 8 9 10 11 12 13 14)
SEED_SPEC="seed5-14"
GAME_COUNT=100
RUN_TS=$(date +%Y%m%d_%H%M)
RUN_TAG="${RUN_TAG:-nostage}"
PARALLEL="${PARALLEL:-4}"

TAG_SUFFIX=""
if [ -n "$RUN_TAG" ]; then
  TAG_SUFFIX="__${RUN_TAG}"
fi

if [ -z "${DAT_ROOT:-}" ]; then
  DAT_ROOT="/HDD/momiyama2/data/study/ntuple_dat/nostage/${SEED_SPEC}/g${GAME_COUNT}/${RUN_TS}${TAG_SUFFIX}"
fi

echo "== Defaults check (training macros) =="
if command -v rg >/dev/null 2>&1; then
  rg -n "STORAGE_FREQUENCY|STORAGE_COUNT|MAX_GAMES" \
    "$BASE_MINI/learning_ntuple_sym.cpp" \
    "$BASE_MINI/learning_ntuple_notsym.cpp"
else
  grep -nE "STORAGE_FREQUENCY|STORAGE_COUNT|MAX_GAMES" \
    "$BASE_MINI/learning_ntuple_sym.cpp" \
    "$BASE_MINI/learning_ntuple_notsym.cpp"
fi
echo "GAME_COUNT=${GAME_COUNT}"
echo "SINGLE_STAGE=1"
echo "DAT_ROOT=${DAT_ROOT}"
echo

compile_train() {
  local src="$1"
  local out="$2"
  local extra="${3:-}"
  echo "Compile: $src -> $out $extra"
  g++ "$src" -O2 -std=c++20 $extra -o "$out"
}

compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_6sym_ns" "-DSINGLE_STAGE"
compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_6notsym_ns" "-DSINGLE_STAGE"
compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_4sym_ns" "-DUSE_4TUPLE -DSINGLE_STAGE"
compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_4notsym_ns" "-DUSE_4TUPLE -DSINGLE_STAGE"

echo "Compile: Play_NT_player.cpp -> play_nt_ns"
g++ "$BASE_NT/Play_NT_player.cpp" -O2 -std=c++20 -DSINGLE_STAGE -o "$BASE_NT/play_nt_ns"
echo

run_one() {
  local tuple="$1"
  local symmetry="$2"
  local train_bin="$3"
  local prefix="$4"
  local seed="$5"

  mkdir -p "$DAT_ROOT" "$LOG_ROOT"
  local log_file="${LOG_ROOT}/log_${tuple}tuple_${symmetry}_seed${seed}_${RUN_TS}${TAG_SUFFIX}.txt"
  echo "== Train: ${tuple}${symmetry} seed=${seed} ==" | tee "$log_file"
  ( cd "$DAT_ROOT" && "$train_bin" "$seed" ) 2>&1 | tee -a "$log_file"
  local evfile="${DAT_ROOT}/${prefix}_${seed}_0.dat"
  if [ ! -f "$evfile" ]; then
    echo "ERROR: evfile not found: $evfile" | tee -a "$log_file" >&2
    exit 1
  fi
  local root="${BOARD_DATA_PARENT}/${RUN_TS}_${tuple}${symmetry}_seed${seed}_g${GAME_COUNT}${TAG_SUFFIX}"
  echo "== Eval: BOARD_DATA_ROOT=${root} ==" | tee -a "$log_file"
  BOARD_DATA_ROOT="$root" "$BASE_NT/play_nt_ns" "$seed" "$GAME_COUNT" "$evfile" "$symmetry" "$tuple" \
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

JOBS=0
for seed in "${SEEDS[@]}"; do
  spawn_job 4 sym "$BASE_MINI/learn_4sym_ns" "4tuple_sym_data" "$seed"
  spawn_job 4 notsym "$BASE_MINI/learn_4notsym_ns" "4tuple_notsym_data" "$seed"
  spawn_job 6 sym "$BASE_MINI/learn_6sym_ns" "6tuple_sym_data" "$seed"
  spawn_job 6 notsym "$BASE_MINI/learn_6notsym_ns" "6tuple_notsym_data" "$seed"
done
wait
