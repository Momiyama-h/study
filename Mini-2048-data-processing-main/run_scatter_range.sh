#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_scatter_range.sh <seed_start> <seed_end> <tuple_list> <stage> [extra args...]

Arguments:
  seed_start   Start seed (inclusive)
  seed_end     End seed (inclusive)
  tuple_list   Comma-separated tuple sizes (e.g. "4,6")
  stage        Learning stage (e.g. 9)

Notes:
  - sym/notsym are both included (no --sym filter is applied).
  - Requires meta.json in each data directory when using --seed/--stage/--tuple.
  - Extra args are passed to: uv run -m graph scatter

Example:
  ./run_scatter_range.sh 5 14 4,6 9 --is-show
EOF
}

if [ "$#" -lt 4 ]; then
  usage
  exit 1
fi

seed_start="$1"
seed_end="$2"
tuple_list="$3"
stage="$4"
shift 4

if ! [[ "$seed_start" =~ ^[0-9]+$ && "$seed_end" =~ ^[0-9]+$ && "$stage" =~ ^[0-9]+$ ]]; then
  echo "seed_start/seed_end/stage must be integers." >&2
  exit 1
fi

if [ "$seed_start" -gt "$seed_end" ]; then
  echo "seed_start must be <= seed_end." >&2
  exit 1
fi

IFS=' ' read -r -a tuple_arr <<< "${tuple_list//,/ }"
if [ "${#tuple_arr[@]}" -eq 0 ]; then
  echo "tuple_list is empty." >&2
  exit 1
fi

seed_arr=()
for ((s = seed_start; s <= seed_end; s++)); do
  seed_arr+=("$s")
done

uv run -m graph scatter \
  --recursive \
  --seed "${seed_arr[@]}" \
  --stage "$stage" \
  --tuple "${tuple_arr[@]}" \
  "$@"
