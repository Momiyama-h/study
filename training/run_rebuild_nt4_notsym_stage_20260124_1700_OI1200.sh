#!/usr/bin/env bash
set -euo pipefail

# Rebuild NT4_notsym (stage only) for 20260124_1700_OI1200__stage

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RUN_NAME_BASE="20260124_1700_OI1200"
RUN_NAME="${RUN_NAME_BASE}__stage"
SEEDS=(${SEEDS:-"5 6 7 8 9 10 11 12 13 14"})

NTUPLE_DAT_ROOT="${NTUPLE_DAT_ROOT:-/HDD/momiyama2/data/study/ntuple_dat}"
LOG_ROOT="${LOG_ROOT:-/HDD/momiyama2/data/study/training_logs}"
BOARD_ROOT="${BOARD_ROOT:-/HDD/momiyama2/data/study/board_data}"

GRAPH_ROOT="${REPO_ROOT}/Mini-2048-data-processing-main"
PERF_DIR="${GRAPH_ROOT}/perfect_player"

echo "== Cleanup NT4_notsym dat/log =="
rm -rf "${NTUPLE_DAT_ROOT}/${RUN_NAME}"/seed*/NT4_notsym
rm -rf "${LOG_ROOT}/${RUN_NAME}"/seed*/NT4_notsym

echo "== Train NT4_notsym (stage only) =="
RUN_NAME_BASE="${RUN_NAME_BASE}" \
STAGE_MODES=stage \
SEEDS="${SEEDS[*]}" \
"${SCRIPT_DIR}/run_train_nt4b_notsym_only.sh"

echo "== Rebuild board_data (NT4_notsym only) =="
"${SCRIPT_DIR}/run_make_board_data_from_dat.sh" \
  --run-name "${RUN_NAME}" \
  --seed-start "${SEEDS[0]}" \
  --seed-end "${SEEDS[-1]}" \
  --ev-stages 9 \
  --tuples 4 \
  --sym-list notsym \
  --overwrite

echo "== PP eval (per-nt) =="
(
  cd "${PERF_DIR}"
  ./run_eval_pp_for_run_name.sh \
    --run-name "${RUN_NAME}" \
    --board-root "${BOARD_ROOT}" \
    --output-mode per-nt \
    --force \
    --parallel 4
)

echo "== Rebuild graphs (NT4 sym/notsym) =="
(
  cd "${GRAPH_ROOT}"
  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph acc --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name acc_stage9
  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph acc-mean --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name acc_mean_stage9
  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph acc-mean-symdiff --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name acc_mean_symdiff_stage9

  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph err-abs --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name err_abs_stage9
  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph err-abs-mean --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name err_abs_mean_stage9
  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph err-rel --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name err_rel_stage9
  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph err-rel-mean --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name err_rel_mean_stage9

  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph surv --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name surv_stage9
  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph surv-mean --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name surv_mean_stage9
  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph surv-diff --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name surv_diff_stage9
  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph surv-diff-mean --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name surv_diff_mean_stage9

  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph evals --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name evals_stage9
  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph evals-mean --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name evals_mean_stage9
  ./run_graph_for_run_name.sh --run-name "${RUN_NAME}" --graph histgram --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym --output-name hist_stage9
)

echo "== Done =="
