#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

LOG_ROOT="${LOG_ROOT:-/HDD/momiyama2/data/study/training_logs}"
RUN_TS="${RUN_TS:-}"
AVESCOPE="${AVESCOPE:-10000}"
OUTPUT_ROOT="${OUTPUT_ROOT:-/HDD/momiyama2/data/study/analysis_outputs/training_scores}"

SEEDS=(${SEEDS:-"15 16 17 18 19 20 21 22 23 24"})
TUPLES=(4 6)
STAGE_TAGS=(stage nostage)
SEED_SPEC="${SEED_SPEC:-seed15-24}"
GAME_COUNT="${GAME_COUNT:-100}"
RUN_NAME_BASE="${RUN_NAME_BASE:-stage_compare_${SEED_SPEC}_g${GAME_COUNT}_${RUN_TS}}"

if [ -z "$RUN_TS" ]; then
  echo "ERROR: RUN_TS is required (e.g. RUN_TS=20250201_1200)." >&2
  exit 1
fi

mkdir -p "${OUTPUT_ROOT}/${RUN_TS}"

for seed in "${SEEDS[@]}"; do
  for tuple in "${TUPLES[@]}"; do
    for stage_tag in "${STAGE_TAGS[@]}"; do
      run_name="${RUN_NAME_BASE}__${stage_tag}"
      sym_log="${LOG_ROOT}/${run_name}/seed${seed}/NT${tuple}_sym/log_${tuple}tuple_sym_seed${seed}_${RUN_TS}__${stage_tag}.txt"
      notsym_log="${LOG_ROOT}/${run_name}/seed${seed}/NT${tuple}_notsym/log_${tuple}tuple_notsym_seed${seed}_${RUN_TS}__${stage_tag}.txt"
      if [ ! -f "$sym_log" ] || [ ! -f "$notsym_log" ]; then
        echo "WARN: missing log(s) for seed=${seed} tuple=${tuple} stage=${stage_tag}" >&2
        echo "  sym:    $sym_log" >&2
        echo "  notsym: $notsym_log" >&2
        continue
      fi
      out_dir="${OUTPUT_ROOT}/${RUN_TS}/tuple${tuple}"
      mkdir -p "$out_dir"
      out_png="${out_dir}/score_seed${seed}_${RUN_TS}__${stage_tag}.png"
      python3 "$SCRIPT_DIR/plot_scores.py" \
        --file1 "$sym_log" \
        --file2 "$notsym_log" \
        --avescope "$AVESCOPE" \
        --output "$out_png"
    done
  done
done
