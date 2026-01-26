#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_export_score_averages_for_run_name.sh --run-name NAME [options]

Options:
  --run-name NAME      run_name under training_logs (required)
  --seed-start N       start seed (optional)
  --seed-end N         end seed (optional)
  --seeds LIST         comma-separated seeds (optional; overrides start/end)
  --tuples LIST        comma-separated tuples (default: 4,6)
  --avescope N         averaging interval (default: 1000)
  --run-ts TS          match logs with this timestamp (optional)
  --log-root DIR       training_logs root (default: /HDD/momiyama2/data/study/training_logs)
  --output-root DIR    output root (default: /HDD/momiyama2/data/study/analysis_outputs/training_scores_csv)
  --dry-run            show actions without executing
USAGE
}

RUN_NAME=""
SEED_START=""
SEED_END=""
SEEDS=""
TUPLES="4,6"
AVESCOPE="1000"
RUN_TS=""
LOG_ROOT="/HDD/momiyama2/data/study/training_logs"
OUTPUT_ROOT="/HDD/momiyama2/data/study/analysis_outputs/training_scores_csv"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name) RUN_NAME="$2"; shift 2;;
    --seed-start) SEED_START="$2"; shift 2;;
    --seed-end) SEED_END="$2"; shift 2;;
    --seeds) SEEDS="$2"; shift 2;;
    --tuples) TUPLES="$2"; shift 2;;
    --avescope) AVESCOPE="$2"; shift 2;;
    --run-ts) RUN_TS="$2"; shift 2;;
    --log-root) LOG_ROOT="$2"; shift 2;;
    --output-root) OUTPUT_ROOT="$2"; shift 2;;
    --dry-run) DRY_RUN=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1"; usage; exit 1;;
  esac
done

if [[ -z "$RUN_NAME" ]]; then
  echo "ERROR: --run-name is required." >&2
  exit 1
fi

IFS=',' read -r -a TUPLE_ARR <<< "$TUPLES"
SEED_ARR=()
if [[ -n "$SEEDS" ]]; then
  IFS=',' read -r -a SEED_ARR <<< "$SEEDS"
else
  if [[ -z "$SEED_START" || -z "$SEED_END" ]]; then
    echo "ERROR: --seeds or --seed-start/--seed-end is required." >&2
    exit 1
  fi
  for ((s=SEED_START; s<=SEED_END; s++)); do
    SEED_ARR+=("$s")
  done
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_BASE="${OUTPUT_ROOT}/${RUN_NAME}"

pick_log() {
  local seed="$1"
  local tuple="$2"
  local sym="$3"
  local dir="${LOG_ROOT}/${RUN_NAME}/seed${seed}/NT${tuple}_${sym}"
  local pattern="log_${tuple}tuple_${sym}_seed${seed}_"
  local glob="${dir}/${pattern}*.txt"
  if [[ -n "$RUN_TS" ]]; then
    glob="${dir}/${pattern}${RUN_TS}*.txt"
  fi
  local match
  match=$(ls -t $glob 2>/dev/null | head -n 1 || true)
  if [[ -z "$match" ]]; then
    echo ""
    return
  fi
  echo "$match"
}

for seed in "${SEED_ARR[@]}"; do
  for tuple in "${TUPLE_ARR[@]}"; do
    for sym in sym notsym; do
      log_file="$(pick_log "$seed" "$tuple" "$sym")"
      if [[ -z "$log_file" ]]; then
        echo "WARN: missing log seed=${seed} tuple=${tuple} sym=${sym}" >&2
        continue
      fi
      out_dir="${OUT_BASE}/NT${tuple}/${sym}"
      out_csv="${out_dir}/score_seed${seed}_NT${tuple}_${sym}.csv"
      if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "DRY-RUN: $log_file -> $out_csv"
        continue
      fi
      mkdir -p "$out_dir"
      python3 "$SCRIPT_DIR/export_score_averages.py" \
        --input "$log_file" \
        --avescope "$AVESCOPE" \
        --output "$out_csv"
    done
  done
done
