#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_scatter_pipeline.sh [options]

Options:
  --seed-start N   Start seed (default: 5)
  --seed-end N     End seed (default: 14)
  --tuples LIST    Comma-separated tuples (default: 4,6)
  --stage N        Learning stage (default: 9)
  --graph NAME     Graph type (default: scatter)
  --output FILE    Output filename (default: scatter.png)
  --show           Show plot window
  --sync           Run "uv sync" before plotting
  -h, --help       Show this help

Notes:
  - Requires board_data with after-state.txt/eval.txt.
  - Requires perfect_player/db2.out (can be a symlink).
  - meta.json is created only if missing.
USAGE
}

SEED_START=5
SEED_END=14
TUPLES="4,6"
STAGE=9
GRAPH="scatter"
OUTPUT="scatter.png"
SHOW=0
DO_SYNC=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --seed-start) SEED_START="$2"; shift 2;;
    --seed-end) SEED_END="$2"; shift 2;;
    --tuples) TUPLES="$2"; shift 2;;
    --stage) STAGE="$2"; shift 2;;
    --graph) GRAPH="$2"; shift 2;;
    --output) OUTPUT="$2"; shift 2;;
    --show) SHOW=1; shift;;
    --sync) DO_SYNC=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1"; usage; exit 1;;
  esac
done

if ! [[ "$SEED_START" =~ ^[0-9]+$ && "$SEED_END" =~ ^[0-9]+$ && "$STAGE" =~ ^[0-9]+$ ]]; then
  echo "seed-start/seed-end/stage must be integers." >&2
  exit 1
fi
if [ "$SEED_START" -gt "$SEED_END" ]; then
  echo "seed-start must be <= seed-end." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR"
BOARD_DIR="$ROOT/board_data"
PP_DIR="$BOARD_DIR/PP"
PERF_DIR="$ROOT/perfect_player"
WRITE_META="$ROOT/write_meta.py"

if [ ! -d "$BOARD_DIR" ]; then
  echo "board_data not found: $BOARD_DIR" >&2
  exit 1
fi
if [ ! -e "$PERF_DIR/db2.out" ]; then
  echo "db2.out not found: $PERF_DIR/db2.out" >&2
  exit 1
fi

IFS=',' read -r -a TUPLE_ARR <<< "$TUPLES"
SEED_ARR=()
for ((s = SEED_START; s <= SEED_END; s++)); do
  SEED_ARR+=("$s")
done

# Create meta.json only if missing.
STAGE="$STAGE" BOARD_DIR="$BOARD_DIR" WRITE_META="$WRITE_META" python3 - <<'PY'
from pathlib import Path
import os
import subprocess

board = Path(os.environ["BOARD_DIR"])
write_meta = os.environ["WRITE_META"]
stage = os.environ["STAGE"]

for run in board.glob("*/*/NT*_*"):
    if not run.is_dir():
        continue
    meta = run / "meta.json"
    if meta.exists():
        continue
    seed_dir = run.parent.name
    if not seed_dir.startswith("seed"):
        continue
    seed = seed_dir.replace("seed", "")
    nt_name = run.name  # NT4_sym / NT6_notsym
    if not nt_name.startswith("NT"):
        continue
    tuple_num = nt_name[2]
    sym = nt_name.split("_", 1)[1]
    evfile = f"{tuple_num}tuple_{sym}_data_{seed}_{stage}.dat"
    subprocess.run(
        ["python3", write_meta, "--board-dir", str(board), str(run), evfile],
        check=True,
    )
PY

# Build eval_after_state if missing.
if [ ! -x "$PERF_DIR/eval_after_state_pp" ]; then
  ( cd "$PERF_DIR" && g++ eval_after_state.cpp -O2 -std=c++20 -mcmodel=large -o eval_after_state_pp )
fi

# Generate PP eval-after-state only when missing.
while IFS= read -r -d '' d; do
  [ -f "$d/after-state.txt" ] || continue
  rel="${d#${BOARD_DIR}/}"
  if [[ "$rel" == PP/* ]]; then
    continue
  fi
  safe="${rel//\//__}"
  out="$PP_DIR/eval-after-state-${safe}.txt"
  if [ -f "$out" ]; then
    continue
  fi
  ( cd "$PERF_DIR" && ./eval_after_state_pp "$rel" )
done < <(find "$BOARD_DIR" -mindepth 3 -maxdepth 3 -type d -print0)

if (( DO_SYNC )); then
  ( cd "$ROOT" && uv sync )
fi

CMD=(uv run -m graph "$GRAPH" --recursive --stage "$STAGE" --tuple "${TUPLE_ARR[@]}" --seed "${SEED_ARR[@]}" --output "$OUTPUT")
if (( SHOW )); then
  CMD+=(--is-show)
fi

( cd "$ROOT" && "${CMD[@]}" )
