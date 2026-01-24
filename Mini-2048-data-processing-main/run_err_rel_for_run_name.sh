#!/usr/bin/env bash
set -euo pipefail
exec "$(dirname "$0")/run_graph_for_run_name.sh" --graph err-rel "$@"
