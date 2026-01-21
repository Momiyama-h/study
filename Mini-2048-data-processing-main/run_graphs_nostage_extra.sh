#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

# Set these at runtime, e.g.
# RUN_ID_5_9=20250201_1200 RUN_ID_10_14=20250201_1200 ./run_graphs_nostage_extra.sh
RUN_ID_5_9="${RUN_ID_5_9:-}"
RUN_ID_10_14="${RUN_ID_10_14:-}"
RUN_SUFFIX="${RUN_SUFFIX:-__nostage}"

if [ -z "$RUN_ID_5_9" ] || [ -z "$RUN_ID_10_14" ]; then
  echo "ERROR: RUN_ID_5_9 and RUN_ID_10_14 must be set."
  echo "Example: RUN_ID_5_9=20250201_1200 RUN_ID_10_14=20250201_1200 $0"
  exit 1
fi

SEEDS=(5 6 7 8 9 10 11 12 13 14)
TUPLES=(4 6)
STAGE="${STAGE:-9}"
GRAPHS=(acc err-abs err-rel evals histgram)

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
  local sym_path="${run_id}_${tuple}sym_seed${seed}_g100${RUN_SUFFIX}/NT${tuple}_sym"
  local notsym_path="${run_id}_${tuple}notsym_seed${seed}_g100${RUN_SUFFIX}/NT${tuple}_notsym"

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
