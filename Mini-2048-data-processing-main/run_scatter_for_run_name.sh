#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_scatter_for_run_name.sh --run-name NAME [options]

Options:
  --run-name NAME      run_name under board_data (required)
  --output-name NAME   output filename without extension (default: scatter)
  --ext EXT            output extension (default: png)
  --seed-start N       start seed (optional)
  --seed-end N         end seed (optional)
  --combine-seeds      combine multiple seeds into a single plot
  --stage N            stage filter (optional)
  --tuples LIST        comma-separated tuples (default: 4,6)
  --sym-list LIST      comma-separated sym list (default: sym,notsym)
  --graph NAME         analysis type (default: scatter)
USAGE
}

RUN_NAME=""
OUTPUT_NAME="scatter"
EXT="png"
SEED_START=""
SEED_END=""
COMBINE_SEEDS=0
STAGE=""
TUPLES="4,6"
SYM_LIST="sym,notsym"
GRAPH="scatter"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name) RUN_NAME="$2"; shift 2;;
    --output-name) OUTPUT_NAME="$2"; shift 2;;
    --ext) EXT="$2"; shift 2;;
    --seed-start) SEED_START="$2"; shift 2;;
    --seed-end) SEED_END="$2"; shift 2;;
    --combine-seeds) COMBINE_SEEDS=1; shift;;
    --stage) STAGE="$2"; shift 2;;
    --tuples) TUPLES="$2"; shift 2;;
    --sym-list) SYM_LIST="$2"; shift 2;;
    --graph) GRAPH="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1"; usage; exit 1;;
  esac
done

if [[ -z "$RUN_NAME" ]]; then
  echo "ERROR: --run-name is required." >&2
  exit 1
fi

REPO="/HDD/momiyama2/repo/Mini-2048-data-processing-main"
BOARD_ROOT="$REPO/board_data"
RUN_DIR="$BOARD_ROOT/$RUN_NAME"
OUT_BASE="/HDD/momiyama2/data/study/analysis_outputs"

if [ ! -d "$RUN_DIR" ]; then
  echo "ERROR: run_name directory not found: $RUN_DIR" >&2
  exit 1
fi

EXT="${EXT#.}"
IFS=',' read -r -a TUPLE_ARR <<< "$TUPLES"
IFS=',' read -r -a SYM_ARR <<< "$SYM_LIST"

run_scatter() {
  local tuple="$1"
  local sym="$2"
  local seed_tag="$3"
  shift 3
  local seed_args=("$@")

  local out_dir="$OUT_BASE/$RUN_NAME/NT${tuple}/${GRAPH}/${sym}"
  mkdir -p "$out_dir"

  local output_file="${OUTPUT_NAME}.${EXT}"
  local output_stem="${output_file%.*}"
  local cmd=(uv run -m graph "$GRAPH" --recursive --intersection "$RUN_NAME" --output "$output_file" --run-name "$RUN_NAME")
  cmd+=(--tuple "$tuple" --sym "$sym")
  if [ -n "$STAGE" ]; then
    cmd+=(--stage "$STAGE")
  fi
  if [ ${#seed_args[@]} -gt 0 ]; then
    cmd+=("${seed_args[@]}")
  fi

  ( cd "$REPO" && "${cmd[@]}" )
  shopt -s nullglob
  matches=("$REPO/output/${output_stem}_"*".${EXT}")
  if [ ${#matches[@]} -gt 0 ]; then
    for f in "${matches[@]}"; do
      mv -f "$f" "$out_dir/$(basename "$f")"
      echo "Saved: $out_dir/$(basename "$f")"
    done
  elif [ -f "$REPO/output/$output_file" ]; then
    mv -f "$REPO/output/$output_file" "$out_dir/$output_file"
    echo "Saved: $out_dir/$output_file"
  else
    echo "ERROR: output not found: $REPO/output/${output_stem}_*.${EXT}" >&2
    shopt -u nullglob
    return 1
  fi
  shopt -u nullglob
}

if [ -n "$SEED_START" ] && [ -n "$SEED_END" ]; then
  if [ "$COMBINE_SEEDS" -eq 1 ]; then
    seed_tag="seed${SEED_START}-${SEED_END}"
    seed_args=()
    for ((s=SEED_START; s<=SEED_END; s++)); do
      seed_args+=(--seed "$s")
    done
    for tuple in "${TUPLE_ARR[@]}"; do
      for sym in "${SYM_ARR[@]}"; do
        run_scatter "$tuple" "$sym" "$seed_tag" "${seed_args[@]}"
      done
    done
  else
    for ((s=SEED_START; s<=SEED_END; s++)); do
      seed_tag="seed${s}"
      seed_args=(--seed "$s")
      for tuple in "${TUPLE_ARR[@]}"; do
        for sym in "${SYM_ARR[@]}"; do
          run_scatter "$tuple" "$sym" "$seed_tag" "${seed_args[@]}"
        done
      done
    done
  fi
else
  seed_tag="allseeds"
  for tuple in "${TUPLE_ARR[@]}"; do
    for sym in "${SYM_ARR[@]}"; do
      run_scatter "$tuple" "$sym" "$seed_tag"
    done
  done
fi
