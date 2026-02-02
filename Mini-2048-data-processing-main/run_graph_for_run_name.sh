#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_graph_for_run_name.sh --run-name NAME --graph GRAPH [options]

Options:
  --run-name NAME      run_name under board_data (required)
  --graph GRAPH        analysis type (required: acc|acc-symdiff|acc-mean|acc-mean-symdiff|err-rel|err-rel-symdiff|err-rel-mean|err-rel-mean-symdiff|err-abs|err-abs-symdiff|err-abs-mean|err-abs-mean-symdiff|surv|surv-mean|surv-mean-symdiff|surv-symdiff|surv-diff|surv-diff-mean|evals|evals-mean|evals-mean-symdiff|scatter|scatter_v2|scatter-symdiff)
  --output-name NAME   output filename without extension (default: <graph>)
  --ext EXT            output extension (default: png)
  --xlim MIN,MAX       x-axis range (e.g. 0,800)
  --ylim MIN,MAX       y-axis range (e.g. 0,1)
  --seed-start N       start seed (optional)
  --seed-end N         end seed (optional)
  --combine-seeds      combine multiple seeds into a single plot
  --stage N            stage filter (optional)
  --tuples LIST        comma-separated tuples (default: 4,6)
  --sym-list LIST      comma-separated sym list (default: sym,notsym)
  --parallel N         max parallel jobs (default: nproc)
  --sample-size N      scatter sample size (<=0 means all points)
  --with-sd            (surv-mean-symdiff only) draw mean±SD band
  --include-pp         (surv-mean / surv-mean-symdiff) include PP mean curve
USAGE
}

RUN_NAME=""
GRAPH=""
OUTPUT_NAME=""
EXT="png"
X_LIM=""
Y_LIM=""
SEED_START=""
SEED_END=""
COMBINE_SEEDS=0
STAGE=""
TUPLES="4,6"
SYM_LIST="sym,notsym"
PARALLEL="$(nproc)"
SAMPLE_SIZE=""
SPLIT_SYM=1
WITH_SD=0
PASS_WITH_SD=0
INCLUDE_PP=0
PASS_INCLUDE_PP=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name) RUN_NAME="$2"; shift 2;;
    --graph) GRAPH="$2"; shift 2;;
    --output-name) OUTPUT_NAME="$2"; shift 2;;
    --ext) EXT="$2"; shift 2;;
    --xlim) X_LIM="$2"; shift 2;;
    --ylim) Y_LIM="$2"; shift 2;;
    --seed-start) SEED_START="$2"; shift 2;;
    --seed-end) SEED_END="$2"; shift 2;;
    --combine-seeds) COMBINE_SEEDS=1; shift;;
    --stage) STAGE="$2"; shift 2;;
    --tuples) TUPLES="$2"; shift 2;;
    --sym-list) SYM_LIST="$2"; shift 2;;
    --parallel) PARALLEL="$2"; shift 2;;
    --sample-size) SAMPLE_SIZE="$2"; shift 2;;
    --with-sd) WITH_SD=1; shift;;
    --include-pp) INCLUDE_PP=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1"; usage; exit 1;;
  esac
done

if [[ -z "$RUN_NAME" || -z "$GRAPH" ]]; then
  echo "ERROR: --run-name and --graph are required." >&2
  exit 1
fi
if [[ "$GRAPH" == *"-mean" ]] || [[ "$GRAPH" == *"-mean-" ]] || [[ "$GRAPH" == "acc-mean-symdiff" ]]; then
  COMBINE_SEEDS=1
fi
if [[ "$GRAPH" == "acc-symdiff" || "$GRAPH" == "acc-mean-symdiff" || "$GRAPH" == "err-abs-symdiff" || "$GRAPH" == "err-abs-mean-symdiff" || "$GRAPH" == "err-rel-symdiff" || "$GRAPH" == "err-rel-mean-symdiff" || "$GRAPH" == "surv-mean-symdiff" || "$GRAPH" == "surv-symdiff" || "$GRAPH" == "evals-mean-symdiff" || "$GRAPH" == "scatter-symdiff" ]]; then
  SPLIT_SYM=0
fi
if [ "$WITH_SD" -eq 1 ]; then
  if [ "$GRAPH" = "surv-mean-symdiff" ]; then
    PASS_WITH_SD=1
  else
    echo "WARNING: --with-sd is only supported for surv-mean-symdiff; ignoring." >&2
  fi
fi
if [ "$INCLUDE_PP" -eq 1 ]; then
  if [ "$GRAPH" = "surv-mean" ] || [ "$GRAPH" = "surv-mean-symdiff" ]; then
    PASS_INCLUDE_PP=1
  else
    echo "WARNING: --include-pp is only supported for surv-mean / surv-mean-symdiff; ignoring." >&2
  fi
fi

if [[ -z "$OUTPUT_NAME" ]]; then
  OUTPUT_NAME="$GRAPH"
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

run_graph() {
  local tuple="$1"
  local sym="$2"
  local seed_tag="$3"
  shift 3
  local seed_args=("$@")

  local out_dir="$OUT_BASE/$RUN_NAME/NT${tuple}/${GRAPH}"
  if [ -n "$sym" ]; then
    out_dir="$out_dir/${sym}"
  fi
  mkdir -p "$out_dir"

  local output_file="${OUTPUT_NAME}.${EXT}"
  if [ -n "$seed_tag" ]; then
    output_file="${OUTPUT_NAME}_${seed_tag}.${EXT}"
  fi
  local run_name_regex
  run_name_regex="$(python3 - <<'PY' "$RUN_NAME"
import re
import sys
name = sys.argv[1]
print("^" + re.escape(name) + "(/|$)")
PY
)"
  local cmd=(uv run -m graph "$GRAPH" --recursive --intersection "$run_name_regex" \
    --output "$output_file" --output-dir "$out_dir")
  if [ -n "$SAMPLE_SIZE" ]; then
    cmd+=(--sample-size "$SAMPLE_SIZE")
  fi
  if [ "$PASS_WITH_SD" -eq 1 ]; then
    cmd+=(--with-sd)
  fi
  if [ "$PASS_INCLUDE_PP" -eq 1 ]; then
    cmd+=(--include-pp)
  fi
  if [ -n "$X_LIM" ]; then
    cmd+=(--xlim "$X_LIM")
  fi
  if [ -n "$Y_LIM" ]; then
    cmd+=(--ylim "$Y_LIM")
  fi
  cmd+=(--tuple "$tuple")
  if [ -n "$sym" ]; then
    cmd+=(--sym "$sym")
  fi
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
  run_graph "$@" &
  JOBS=$((JOBS+1))
  if [ "$JOBS" -ge "$PARALLEL" ]; then
    wait -n
    JOBS=$((JOBS-1))
  fi
}

if [ -n "$SEED_START" ] && [ -n "$SEED_END" ]; then
  if [ "$COMBINE_SEEDS" -eq 1 ]; then
    seed_args=(--seed)
    for ((s=SEED_START; s<=SEED_END; s++)); do
      seed_args+=("$s")
    done
    for tuple in "${TUPLE_ARR[@]}"; do
      if [ "$SPLIT_SYM" -eq 1 ]; then
        for sym in "${SYM_ARR[@]}"; do
          spawn_job "$tuple" "$sym" "seed${SEED_START}-${SEED_END}" "${seed_args[@]}"
        done
      else
        spawn_job "$tuple" "" "seed${SEED_START}-${SEED_END}" "${seed_args[@]}"
      fi
    done
  else
    for ((s=SEED_START; s<=SEED_END; s++)); do
      seed_args=(--seed "$s")
      for tuple in "${TUPLE_ARR[@]}"; do
        if [ "$SPLIT_SYM" -eq 1 ]; then
          for sym in "${SYM_ARR[@]}"; do
            spawn_job "$tuple" "$sym" "seed${s}" "${seed_args[@]}"
          done
        else
          spawn_job "$tuple" "" "seed${s}" "${seed_args[@]}"
        fi
      done
    done
  fi
else
  for tuple in "${TUPLE_ARR[@]}"; do
    if [ "$SPLIT_SYM" -eq 1 ]; then
      for sym in "${SYM_ARR[@]}"; do
        spawn_job "$tuple" "$sym" ""
      done
    else
      spawn_job "$tuple" "" ""
    fi
  done
fi

wait
