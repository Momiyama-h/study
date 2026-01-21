#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

RUN_ID_5_9="20260116_0419"
RUN_ID_10_14="20260121_0035"

SEEDS=(5 6 7 8 9 10 11 12 13 14)
TUPLES=(4 6)
STAGE=9
GRAPHS=(acc err-rel err-abs surv surv-diff histgram evals scatter_v2)

INTERSECTION_PREFIXES=(
  "${RUN_ID_5_9}_"
  "${RUN_ID_10_14}_"
)

run_id_for_seed() {
  local seed="$1"
  if [ "$seed" -le 9 ]; then
    printf "%s" "$RUN_ID_5_9"
  else
    printf "%s" "$RUN_ID_10_14"
  fi
}

run_graph_set() {
  local sym="$1"
  for g in "${GRAPHS[@]}"; do
    uv run -m graph "$g" \
      --recursive \
      --stage "$STAGE" \
      --seed "${SEEDS[@]}" \
      --tuple "${TUPLES[@]}" \
      --sym "$sym" \
      --intersection "${INTERSECTION_PREFIXES[@]}" \
      --output "${g}_${sym}_s${STAGE}.png"
  done
}

run_acc_diff() {
  local seed="$1"
  local tuple="$2"
  local run_id
  run_id="$(run_id_for_seed "$seed")"

  uv run -m graph acc-diff \
    --recursive \
    --stage "$STAGE" \
    --intersection "${run_id}_${tuple}sym_seed${seed}_g100/NT${tuple}_sym" \
                   "${run_id}_${tuple}notsym_seed${seed}_g100/NT${tuple}_notsym" \
    --output "acc-diff_t${tuple}_seed${seed}_s${STAGE}.png"
}

cd "$BASE_DIR"

run_graph_set sym
run_graph_set notsym

for seed in "${SEEDS[@]}"; do
  for tuple in "${TUPLES[@]}"; do
    run_acc_diff "$seed" "$tuple"
  done
done
