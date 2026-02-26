#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_top_updatecounts.sh --run-name NAME --dat-root PATH --tuple {4|5|6} \
    --seed N --ev-stage N --sym MODE [options]

Required:
  --run-name NAME      run_name (under dat_root)
  --dat-root PATH      base path of ntuple_dat
  --tuple N            tuple size: 4 / 5 / 6
  --seed N             train seed
  --ev-stage N         ev stage (dat suffix stage, e.g. 9)
  --sym MODE           sym mode:
                        sym | notsym |
                        rotate | rotate_notsym |
                        rot180 | rot180_notsym |
                        diag | diag_notsym

Optional:
  --table-stage X      table stage to read: 0/1 or all (default: all)
  --top-k N            output top-k (default: 20)
  --nt4a               use NT4A header layout for tuple=4
  --build-dir PATH     build dir (default: training/bin)
  --keep-bin           do not rebuild if existing binary can be reused
  -h, --help           show this help
USAGE
}

RUN_NAME=""
DAT_ROOT=""
TUPLE=""
SEED=""
EV_STAGE=""
TABLE_STAGE="all"
SYM_MODE=""
TOP_K=20
USE_NT4A=0
KEEP_BIN=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/bin"
SRC="${SCRIPT_DIR}/show_top_updatecounts.cpp"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-name) RUN_NAME="$2"; shift 2;;
    --dat-root) DAT_ROOT="$2"; shift 2;;
    --tuple) TUPLE="$2"; shift 2;;
    --seed) SEED="$2"; shift 2;;
    --ev-stage|--stage) EV_STAGE="$2"; shift 2;;
    --table-stage) TABLE_STAGE="$2"; shift 2;;
    --sym) SYM_MODE="$2"; shift 2;;
    --top-k) TOP_K="$2"; shift 2;;
    --nt4a) USE_NT4A=1; shift;;
    --build-dir) BUILD_DIR="$2"; shift 2;;
    --keep-bin) KEEP_BIN=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1" >&2; usage; exit 1;;
  esac
done

if [[ -z "$RUN_NAME" || -z "$DAT_ROOT" || -z "$TUPLE" || -z "$SEED" || -z "$EV_STAGE" || -z "$SYM_MODE" ]]; then
  echo "ERROR: missing required options." >&2
  usage
  exit 1
fi

if [[ "$TUPLE" != "4" && "$TUPLE" != "5" && "$TUPLE" != "6" ]]; then
  echo "ERROR: --tuple must be 4, 5, or 6." >&2
  exit 1
fi

case "$SYM_MODE" in
  sym|notsym|rotate|rotate_notsym|rot180|rot180_notsym|diag|diag_notsym) ;;
  *)
    echo "ERROR: unsupported --sym: $SYM_MODE" >&2
    exit 1
    ;;
esac

mkdir -p "$BUILD_DIR"

tuple_flags=()
if [[ "$TUPLE" == "4" ]]; then
  tuple_flags+=("-DUSE_4TUPLE")
  if [[ "$USE_NT4A" -eq 1 ]]; then
    tuple_flags+=("-DNT4A")
  fi
elif [[ "$TUPLE" == "5" ]]; then
  tuple_flags+=("-DUSE_5TUPLE")
fi

mode_flags=()
mode_tag=""
case "$SYM_MODE" in
  sym|rotate|rot180|diag)
    mode_flags+=("-DMODE_SYM_LIKE")
    mode_tag="sym_like"
    ;;
  notsym)
    mode_flags+=("-DMODE_NOTSYM")
    mode_tag="notsym"
    ;;
  rotate_notsym)
    mode_flags+=("-DMODE_ROTATE_NOTSYM")
    mode_tag="rotate_notsym"
    ;;
  rot180_notsym)
    mode_flags+=("-DMODE_ROT180_NOTSYM")
    mode_tag="rot180_notsym"
    ;;
  diag_notsym)
    mode_flags+=("-DMODE_DIAG_NOTSYM")
    mode_tag="diag_notsym"
    ;;
esac

nt4a_tag=""
if [[ "$USE_NT4A" -eq 1 ]]; then
  nt4a_tag="_nt4a"
fi
BIN="${BUILD_DIR}/show_top_updatecounts_nt${TUPLE}_${mode_tag}${nt4a_tag}"

if [[ "$KEEP_BIN" -eq 0 || ! -x "$BIN" || "$SRC" -nt "$BIN" ]]; then
  echo "Compile: $SRC -> $BIN"
  g++ -O3 -std=c++17 "$SRC" "${tuple_flags[@]}" "${mode_flags[@]}" -o "$BIN"
fi

DAT_DIR="${DAT_ROOT}/${RUN_NAME}/seed${SEED}/NT${TUPLE}_${SYM_MODE}"
DAT_FILE="${TUPLE}tuple_${SYM_MODE}_data_${SEED}_${EV_STAGE}.dat"
DAT_PATH="${DAT_DIR}/${DAT_FILE}"

if [[ ! -f "$DAT_PATH" ]]; then
  echo "ERROR: dat not found: $DAT_PATH" >&2
  exit 2
fi

echo "Running: $BIN"
echo "  dat:   $DAT_PATH"
echo "  table-stage: $TABLE_STAGE"
echo "  top-k: $TOP_K"
echo
"$BIN" "$DAT_PATH" "$TABLE_STAGE" "$TOP_K"
