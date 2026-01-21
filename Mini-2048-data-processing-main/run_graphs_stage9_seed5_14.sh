#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

RUN_ID_5_9="20260116_0419"
RUN_ID_10_14="20260121_0035"

SEEDS=(5 6 7 8 9 10 11 12 13 14)
TUPLES=(4 6)
STAGE=9
GRAPHS=(acc acc-diff err-rel err-abs surv surv-diff evals scatter_v2)

run_id_for_seed() {
  local seed="$1"
  if [ "$seed" -le 9 ]; then
    printf "%s" "$RUN_ID_5_9"
  else
    printf "%s" "$RUN_ID_10_14"
  fi
}

run_pair_graph() {
  local graph="$1"
  local seed="$2"
  local tuple="$3"
  local run_id
  run_id="$(run_id_for_seed "$seed")"
  local sym_path="${run_id}_${tuple}sym_seed${seed}_g100/NT${tuple}_sym"
  local notsym_path="${run_id}_${tuple}notsym_seed${seed}_g100/NT${tuple}_notsym"

  uv run -m graph "$graph" \
    --recursive \
    --stage "$STAGE" \
    --intersection "$sym_path" \
                   "$notsym_path" \
    --output "${graph}_t${tuple}_seed${seed}_s${STAGE}.png"
}

cd "$BASE_DIR"

for seed in "${SEEDS[@]}"; do
  for tuple in "${TUPLES[@]}"; do
    for graph in "${GRAPHS[@]}"; do
      run_pair_graph "$graph" "$seed" "$tuple"
    done
  done
done
