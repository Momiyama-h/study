#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE_MINI="${BASE_MINI:-$REPO_ROOT/training}"
BASE_NT="${BASE_NT:-$REPO_ROOT/Mini-2048-data-processing-main/NT}"
DAT_ROOT="${DAT_ROOT:-/HDD/momiyama2/data/study/ntuple_dat}"
LOG_ROOT="${LOG_ROOT:-/HDD/momiyama2/data/study/training_logs}"
BOARD_DATA_PARENT="${BOARD_DATA_PARENT:-${BASE_NT}/../board_data}"

SEEDS=(10 11 12 13 14)
GAME_COUNT=100
RUN_TS=$(date +%Y%m%d_%H%M)
PARALLEL="${PARALLEL:-4}"

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
echo

compile_train() {
  local src="$1"
  local out="$2"
  local extra="${3:-}"
  echo "Compile: $src -> $out $extra"
  g++ "$src" -O2 -std=c++20 $extra -o "$out"
}

compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_6sym"
compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_6notsym"
compile_train "$BASE_MINI/learning_ntuple_sym.cpp" "$BASE_MINI/learn_4sym" "-DUSE_4TUPLE"
compile_train "$BASE_MINI/learning_ntuple_notsym.cpp" "$BASE_MINI/learn_4notsym" "-DUSE_4TUPLE"

echo "Compile: Play_NT_player.cpp -> play_nt"
g++ "$BASE_NT/Play_NT_player.cpp" -O2 -std=c++20 -o "$BASE_NT/play_nt"
echo

run_one() {
  local tuple="$1"
  local symmetry="$2"
  local train_bin="$3"
  local prefix="$4"
  local seed="$5"

  mkdir -p "$DAT_ROOT" "$LOG_ROOT"
  local log_file="${LOG_ROOT}/log_${tuple}tuple_${symmetry}_seed${seed}_${RUN_TS}.txt"
  echo "== Train: ${tuple}${symmetry} seed=${seed} ==" | tee "$log_file"
  ( cd "$DAT_ROOT" && "$train_bin" "$seed" ) 2>&1 | tee -a "$log_file"
  local evfile="${DAT_ROOT}/${prefix}_${seed}_0.dat"
  if [ ! -f "$evfile" ]; then
    echo "ERROR: evfile not found: $evfile" | tee -a "$log_file" >&2
    exit 1
  fi
  local root="${BOARD_DATA_PARENT}/${RUN_TS}_${tuple}${symmetry}_seed${seed}_g${GAME_COUNT}"
  echo "== Eval: BOARD_DATA_ROOT=${root} ==" | tee -a "$log_file"
  BOARD_DATA_ROOT="$root" "$BASE_NT/play_nt" "$seed" "$GAME_COUNT" "$evfile" "$symmetry" "$tuple" \
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
  spawn_job 4 sym "$BASE_MINI/learn_4sym" "4tuple_sym_data" "$seed"
  spawn_job 4 notsym "$BASE_MINI/learn_4notsym" "4tuple_notsym_data" "$seed"
  spawn_job 6 sym "$BASE_MINI/learn_6sym" "6tuple_sym_data" "$seed"
  spawn_job 6 notsym "$BASE_MINI/learn_6notsym" "6tuple_notsym_data" "$seed"
done
wait

