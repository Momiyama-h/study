#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

rm -f "$REPO_ROOT/Mini-2048-data-processing-main/graph/config.json.lock"
rm -f "$REPO_ROOT/Mini-2048-data-processing-main/NT/play_nt"
rm -f "$REPO_ROOT/Mini-2048-data-processing-main/NT/play_nt_ns"
rm -f "$REPO_ROOT/Mini-2048-data-processing-main/perfect_player/eval_state_pp"
rm -f "$REPO_ROOT/Mini-2048-data-processing-main/perfect_player/eval_after_state_pp"

printf 'Removed build artifacts under %s\n' "$REPO_ROOT"
