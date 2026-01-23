# シェルスクリプト解説

このドキュメントは、リポジトリ内の .sh の用途と使い方をまとめたものです。パスや出力先は現行コードの挙動に基づいています。

## training/

### run_train_4patterns_10seeds_trainonly.sh
- 目的: 学習のみ実行（board_data/eval は作成しない）
- 出力:
  - .dat: /HDD/momiyama2/data/study/ntuple_dat/<run_name>/seed<seed>/NT{4|6}_{sym|notsym}/
  - log: /HDD/momiyama2/data/study/training_logs/<run_name>/seed<seed>/NT{4|6}_{sym|notsym}/
- 主な指定（環境変数）:
  - RUN_NAME_BASE（推奨）
  - SEEDS（例: "5 6 7 8 9 10 11 12 13 14"）
  - PARALLEL, STDOUT_LOG, NTUPLE_DAT_ROOT, LOG_ROOT
- 例:
  - PARALLEL=$(nproc) RUN_NAME_BASE=20260123_0300 SEEDS="5 6 7 8 9 10 11 12 13 14" ./training/run_train_4patterns_10seeds_trainonly.sh

### run_train_eval_4patterns_10seeds_nostage.sh
- 目的: 学習（nostage）＋ board_data/meta.json 生成
- 出力:
  - .dat: ntuple_dat/<run_name>/seed<seed>/NT*_*（stage 0）
  - log: training_logs/<run_name>/seed<seed>/NT*_*（log_*.txt）
  - board_data: board_data/<run_name>/seed<seed>/NT*_*（state/after-state/eval/meta.json）
- 主な指定（環境変数）:
  - RUN_NAME, PARALLEL, STDOUT_LOG, NTUPLE_DAT_ROOT, LOG_ROOT, BOARD_DATA_PARENT

### run_train_eval_4patterns_10seeds_stagecompare.sh
- 目的: 学習（stage + nostage）＋ board_data/meta.json 生成
- 出力: 上記と同じ構成、run_name は __stage / __nostage が付く
- 主な指定（環境変数）:
  - RUN_NAME_BASE, SEEDS, STAGE_MODES, EV_STAGE, PARALLEL, NTUPLE_DAT_ROOT, LOG_ROOT, BOARD_DATA_PARENT

### run_train_eval_4patterns_5seeds.sh
- 目的: seed数を減らした旧版
- 出力: train+eval 系と同様

### run_make_board_data_from_dat.sh
- 目的: 既存 .dat から board_data を作成
- デフォルト: game_count=10000、meta.json は不足分のみ作成（不一致時は警告のみ）
- 必須引数:
  - --run-name NAME
  - --seed-start N --seed-end N
  - --ev-stages LIST（例: 9 または 0,1,2）
- オプション:
  - --force-meta: meta.json の不一致を検出した場合に上書き再生成
- 例:
  - ./training/run_make_board_data_from_dat.sh --run-name 20260123_0300__stage --seed-start 5 --seed-end 14 --ev-stages 9

### run_plot_scores_stagecompare.sh
- 目的: 学習ログから seed別のスコア推移グラフを出力
- 入力: training_logs/<run_name>/seed<seed>/NT*_* の log_*.txt
- 出力: analysis_outputs/training_scores/<RUN_TS>/tuple{4,6}/

### run_plot_and_summary.sh
- 目的: LOG_ROOT 配下のログをまとめて可視化・要約

## Mini-2048-data-processing-main/

### run_scatter_for_run_name.sh
- 目的: uv graph を実行し、analysis_outputs に保存
- 出力先:
  - /HDD/momiyama2/data/study/analysis_outputs/<run_name>/NT{4|6}/{graph}/{sym|notsym}/
- デフォルト: seedごとに個別出力（複数seed指定時も分割）
  - まとめる場合は --combine-seeds を指定
- 例:
  - ./run_scatter_for_run_name.sh --run-name 20260123_0300__stage --seed-start 5 --seed-end 14 --stage 9 --output-name scatter_stage9

### run_scatter_pipeline.sh
- 目的: meta.json 生成（不足分のみ）→ PP評価 → グラフ出力
- 前提: board_data に after-state.txt/eval.txt があること、perfect_player/db2.out があること

### run_scatter_range.sh
- 目的: 範囲指定の scatter（旧版）

### run_graphs_stage9_seed5_14.sh
- 目的: stage9 の一括グラフ（旧レイアウト対応）

### run_graphs_nostage_scatter_symdiff.sh
- 目的: nostage の scatter + sym/notsym比較（旧レイアウト対応）

### run_graphs_nostage_extra.sh
- 目的: nostage の追加グラフ（旧レイアウト対応）

### run_graphs.sh
- 目的: 一括グラフの汎用スクリプト

## perfect_player/

### run_eval_pp_for_run_name.sh
- 目的: run_name 配下の board_data から eval-state / eval-after-state を作成
- デフォルト出力: per-nt（board_data/<run_name>/seed<seed>/NT*_/eval-*.txt）
- --output-mode pp を指定すると board_data/PP/ に安全名で出力
- 例:
  - ./perfect_player/run_eval_pp_for_run_name.sh --run-name 20260123_0300__stage

### cp.sh
- 目的: PP 関連のコピー補助（旧版）

## NT_all_tuple/

### compile_all.sh, play_*.sh, fix_*.sh
- 目的: NT_all_tuple 向けの旧ユーティリティ
- 現行の NT4/NT6 パイプラインでは未使用

## mcts/ / Expectimax/

### mcts/run.sh, mcts/run-2.sh, Expectimax/run.sh
- 目的: MCTS/Expectimax 用の旧ランナー

## 補足
- board_data は Mini-2048-data-processing-main/board_data を前提に探索されます（symlink 推奨）。
- `--seed/--stage/--tuple` の絞り込みは meta.json が必要です。
- scatter は PP 評価ファイルが必要（per-nt または board_data/PP）。
