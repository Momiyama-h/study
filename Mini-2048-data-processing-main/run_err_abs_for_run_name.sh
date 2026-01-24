#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_err_abs_for_run_name.sh --run-name NAME [options]

Options:
  --run-name NAME      run_name under board_data (required)
  --output-name NAME   output filename without extension (default: err_abs)
  --ext EXT            output extension (default: png)
  --seed-start N       start seed (optional)
  --seed-end N         end seed (optional)
  --combine-seeds      combine multiple seeds into a single plot
  --stage N            stage filter (optional)
  --tuples LIST        comma-separated tuples (default: 4,6)
  --sym-list LIST      comma-separated sym list (default: sym,notsym)
  --parallel N         max parallel jobs (default: nproc)
USAGE
}

RUN_NAME=""
OUTPUT_NAME="err_abs"
EXT="png"
SEED_START=""
SEED_END=""
COMBINE_SEEDS=0
STAGE=""
TUPLES="4,6"
SYM_LIST="sym,notsym"
PARALLEL="$(nproc)"

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
    --parallel) PARALLEL="$2"; shift 2;;
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

JOBS=0

run_err_abs() {
  local tuple="$1"
  local sym="$2"
  shift 2
  local seed_args=("$@")

  local out_dir="$OUT_BASE/$RUN_NAME/NT${tuple}/err-abs/${sym}"
  mkdir -p "$out_dir"

  local output_file="${OUTPUT_NAME}.${EXT}"
  local cmd=(uv run -m graph err-abs --recursive --intersection "$RUN_NAME" \
    --output "$output_file" --output-dir "$out_dir")
  cmd+=(--tuple "$tuple" --sym "$sym")
  if [ -n "$STAGE" ]; then
    cmd+=(--stage "$STAGE")
  fi
  if [ ${#seed_args[@]} -gt 0 ]; then
    cmd+=("${seed_args[@]}")
  fi

  ( cd "$REPO" && "${cmd[@]}" )
  echo "Saved: $out_dir (by --output-dir)"
}

spawn_job() {
  run_err_abs "$@" &
  JOBS=$((JOBS+1))
  if [ "$JOBS" -ge "$PARALLEL" ]; then
    wait -n
    JOBS=$((JOBS-1))
  fi
}

if [ -n "$SEED_START" ] && [ -n "$SEED_END" ]; then
  if [ "$COMBINE_SEEDS" -eq 1 ]; then
    seed_args=()
    for ((s=SEED_START; s<=SEED_END; s++)); do
      seed_args+=(--seed "$s")
    done
    for tuple in "${TUPLE_ARR[@]}"; do
      for sym in "${SYM_ARR[@]}"; do
        spawn_job "$tuple" "$sym" "${seed_args[@]}"
      done
    done
  else
    for ((s=SEED_START; s<=SEED_END; s++)); do
      seed_args=(--seed "$s")
      for tuple in "${TUPLE_ARR[@]}"; do
        for sym in "${SYM_ARR[@]}"; do
          spawn_job "$tuple" "$sym" "${seed_args[@]}"
        done
      done
    done
  fi
else
  for tuple in "${TUPLE_ARR[@]}"; do
    for sym in "${SYM_ARR[@]}"; do
      spawn_job "$tuple" "$sym"
    done
  done
fi

wait
