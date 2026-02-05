# シェルスクリプト解説


## 統一ラッパー（推奨）

### 方針
- 学習系と「学習＋評価＋board_data」系は、統一ラッパーで起動する
- 既存の細分化スクリプトは温存しつつ、将来的に置換可能

### 実行内容の決定ルール
- どのタプルを動かすかは `--tuples` または `TUPLES` で決定
  - 4/6 → NT4/NT6 を実行
  - 5 → NT5a を実行（nostage-only は不可）
- stage/nostage は `--stage-mode` で決定（stage|nostage|both）
- seed 範囲は `--seed-start/--seed-end` か `--seeds` で決定
- run_name は `RUN_NAME_BASE` + `__stage` / `__nostage`

### 出力先ルール
- 学習のみ (`run_train_only.sh`)
  - .dat: `ntuple_dat/<run_name>/seed<seed>/NT{4|5|6}_{sym|notsym}/`
  - log: `training_logs/<run_name>/seed<seed>/NT{4|5|6}_{sym|notsym}/`
- 学習＋評価＋board_data (`run_train_eval_boarddata.sh`)
  - 上記に加えて `board_data/<run_name>/seed<seed>/NT{4|6}_{sym|notsym}/`
  - meta.json は board_data 生成時に作成

このドキュメントは、リポジトリ内の .sh の用途と使い方をまとめたものです。パスや出力先は現行コードの挙動に基づいています。

## training/

### run_train_unified.sh
- 目的: 学習のみを一つのスクリプトで実行（NT4/NT5/NT6 を任意に選択）
- 主な引数:
  - --run-name-base NAME
  - --stage-mode stage|nostage|both（デフォルト: stage）
  - --seed-start / --seed-end / --seeds
  - --tuples "4 5 6"（任意の組み合わせ）
  - --parallel / --stdout-log / --init-ev
  - --policy greedy|expecti3（デフォルト: greedy）
- 出力:
  - .dat: /HDD/momiyama2/data/study/ntuple_dat/<run_name>/seed<seed>/NT{4|5|6}_{sym|notsym}/
  - log: /HDD/momiyama2/data/study/training_logs/<run_name>/seed<seed>/NT{4|5|6}_{sym|notsym}/
- 補足:
  - `--policy expecti3` を指定すると `run_name` に `__policy=expecti3` が自動付与されます。
- 例:
  - ./training/run_train_unified.sh --run-name-base 20260128_2000_OI1200 --stage-mode stage --seed-start 10 --seed-end 14 --tuples "4 5 6" --parallel 8
  - ./training/run_train_unified.sh --run-name-base 20260128_2000_OI1200 --policy expecti3 --stage-mode nostage --seed-start 5 --seed-end 5 --tuples "4" --parallel 1

### run_train_only.sh
- 目的: 学習のみをまとめて実行するラッパー（NT4/NT6、必要ならNT5a）
- 入力: training/run_train_4patterns_10seeds_trainonly.sh / run_train_nt5a_trainonly.sh を内部呼び出し
- 主な引数:
  - --run-name-base NAME
  - --stage-mode stage|nostage|both（デフォルト: stage）
  - --seed-start / --seed-end / --seeds
  - --tuples "4 6"（5 を含むと NT5a を実行）
  - --parallel / --parallel-by-seed
  - --stdout-log / --init-ev
- 例:
  - ./training/run_train_only.sh --run-name-base 20260128_2000_OI1200 --stage-mode stage --seed-start 10 --seed-end 14 --tuples "4 6" --parallel 8

### run_train_4patterns_10seeds_trainonly.sh
- 状態: 旧スクリプト（推奨: run_train_only.sh）
- 目的: 学習のみ実行（board_data/eval は作成しない）
- 出力:
  - .dat: /HDD/momiyama2/data/study/ntuple_dat/<run_name>/seed<seed>/NT{4|6}_{sym|notsym}/
  - log: /HDD/momiyama2/data/study/training_logs/<run_name>/seed<seed>/NT{4|6}_{sym|notsym}/
- 主な指定（環境変数）:
  - RUN_NAME_BASE（推奨。run_name は `__stage` / `__nostage` が付与される）
  - SEEDS（例: "5 6 7 8 9 10 11 12 13 14"）
  - STAGE_MODE（stage|nostage|both）, STAGE_MODES（例: "stage,nostage"）
  - NTUPLES（例: "4 6"）
  - PARALLEL, STDOUT_LOG, NTUPLE_DAT_ROOT, LOG_ROOT
- 主な指定（引数）:
  - --stage-only / --nostage
  - --stage-mode MODE（stage|nostage|both）
  - --stage-modes LIST（例: "stage,nostage"）
  - --tuples LIST（例: "4 6"）
  - --parallel-by-seed / --sequential
- 例:
  - PARALLEL=$(nproc) RUN_NAME_BASE=20260123_0300 SEEDS="5 6 7 8 9 10 11 12 13 14" STAGE_MODE=stage NTUPLES="4 6" ./training/run_train_4patterns_10seeds_trainonly.sh

### run_make_board_data_from_dat.sh
- 目的: 既存 .dat から board_data を作成
- デフォルト: game_count=10000、meta.json は不足分のみ作成（不一致時は警告のみ）
- 必須引数:
  - --run-name NAME
  - --seed-start N --seed-end N
  - --ev-stages LIST（例: 9 または 0,1,2）
- 追加オプション:
  - --dat-run-name NAME: dat 探索用の run_name（省略時は --run-name と同じ）
- オプション:
  - --force-meta: meta.json の不一致を検出した場合に上書き再生成
  - --overwrite: 既存の board_data を削除して再生成
  - --single-stage / --nostage: stage0 固定で評価（play_nt_ns を使用）
- 備考:
  - play_nt が無い場合は自動ビルド
  - play_nt_ns が無い場合は -DSINGLE_STAGE で自動ビルド
- 例:
  - ./training/run_make_board_data_from_dat.sh --run-name 20260123_0300__stage --seed-start 5 --seed-end 14 --ev-stages 9
  - ./training/run_make_board_data_from_dat.sh --run-name 20260123_0300__nostage --seed-start 5 --seed-end 14 --ev-stages 9 --nostage --overwrite

### make_progress_counts.py
- 目的: board_data の `state.txt` から progress 別の盤面数を集計し、CSV/グラフを出力
- 入力: `board_data/<run_name>/seed*/NT*_*` 配下の `state.txt`
- 出力:
  - `analysis_outputs/<run_name>/progress_counts/`
  - `progress_count_seedX_NT*_sym.csv` / `.png` (or `--ext pdf`)
- 主な引数:
  - --run-name NAME（必須）
  - --board-root PATH（省略可、デフォルト: /HDD/momiyama2/data/study/board_data）
  - --analysis-root PATH（省略可、デフォルト: /HDD/momiyama2/data/study/analysis_outputs）
  - --format csv|plot|both（デフォルト: both）
  - --ext png|pdf（デフォルト: png）
  - --grid-y（横線グリッド）
- 例:
  - python3 ./training/make_progress_counts.py --run-name 20260129_2000_OI1200__stage --format both --grid-y

### run_plot_scores_stagecompare.sh
- 目的: 学習ログから seed別のスコア推移グラフを出力
- 入力: training_logs/<run_name>/seed<seed>/NT*_* の log_*.txt
- 出力: analysis_outputs/training_scores/<RUN_TS>/tuple{4,6}/

### run_plot_scores_for_run_name.sh
- 目的: run_name 単位で seed別・NT別のスコア推移グラフを出力（sym/notsym を同一グラフ）
- 入力: training_logs/<run_name>/seed<seed>/NT*_* の log_*.txt
- 出力: analysis_outputs/training_scores/<run_name>/NT{4|6}/score_seed{seed}_NT{tuple}.png
- 主な引数:
  - --run-name NAME（必須）
  - --seed-start N / --seed-end N または --seeds LIST（必須）
  - --tuples LIST（省略可、デフォルト: 4,6）
  - --avescope N（省略可、デフォルト: 10000）
  - --run-ts TS（省略可、timestamp を含むログのみ対象）
  - --log-root / --output-root（省略可）
- 例:
  - ./training/run_plot_scores_for_run_name.sh --run-name 20260123_0300__nostage --seed-start 5 --seed-end 14 --avescope 10000

### run_export_score_averages_for_run_name.sh
- 目的: run_name 単位で seed別・NT別の平均スコアをCSVに出力（sym/notsym 別）
- 入力: training_logs/<run_name>/seed<seed>/NT*_* の log_*.txt
- 出力: analysis_outputs/training_scores_csv/<run_name>/NT{4|6}/{sym|notsym}/score_seed{seed}_NT{tuple}_{sym}.csv
- 主な引数:
  - --run-name NAME（必須）
  - --seed-start N / --seed-end N または --seeds LIST（必須）
  - --tuples LIST（省略可、デフォルト: 4,6）
  - --avescope N（省略可、デフォルト: 1000）
  - --run-ts TS（省略可、timestamp を含むログのみ対象）
  - --log-root / --output-root（省略可）
- 例:
  - ./training/run_export_score_averages_for_run_name.sh --run-name 20260123_0300__nostage --seed-start 5 --seed-end 14 --avescope 1000

### run_eval_scores_from_dat.sh
- 目的: 学習済み .dat を読み込み、指定ゲーム数（デフォルト: 10000）をプレイして、1000ゲーム単位の平均/標準偏差をCSVに出力
- 入力: ntuple_dat/<run_name>/seed<seed>/NT{4|6}_{sym|notsym}/ の *.dat
- 出力: analysis_outputs/training_scores_from_dat/<run_name>/NT{4|6}/{sym|notsym}/score_seed<seed>_NT{tuple}_{sym}_stage<stage>.csv
- 主な引数:
  - --run-name NAME（必須）
  - --seed-start N / --seed-end N または --seeds LIST（必須）
  - --stage N（省略可、デフォルト: 9）
  - --tuples LIST（省略可、デフォルト: 4,6）
  - --sym-list LIST（省略可、デフォルト: sym,notsym）
  - --games N（省略可、デフォルト: 10000）
  - --avescope N（省略可、デフォルト: 1000）
  - --parallel N（省略可、デフォルト: 1）
  - --nostage（nostage dat 用に SINGLE_STAGE 固定で実行）
  - --dat-root / --output-root（省略可）
- 例:
  - ./training/run_eval_scores_from_dat.sh --run-name 20260124_1700_OI1200__stage --seed-start 5 --seed-end 14 --stage 9 --tuples 4 --sym-list sym,notsym
  - ./training/run_eval_scores_from_dat.sh --run-name 20260123_0300__nostage --seed-start 5 --seed-end 14 --stage 9 --nostage

### run_plot_and_summary.sh
- 目的: LOG_ROOT 配下のログをまとめて可視化・要約


### run_err_abs_for_run_name.sh
- 目的: run_name 配下の board_data から err-abs を生成
- 必須引数:
  - --run-name NAME
- オプション:
  - --output-name NAME: 出力ファイルのベース名（デフォルト: err_abs）
  - --ext EXT: 拡張子（デフォルト: png）
  - --seed-start N / --seed-end N: seed 範囲指定
  - --combine-seeds: 複数seedを1枚にまとめる
  - --stage N: meta.json の stage で絞り込み
  - --tuples LIST: 4,6 など
  - --sym-list LIST: sym,notsym など
  - --parallel N: 並列数（デフォルト: nproc）
- 出力先:
  - /HDD/momiyama2/data/study/analysis_outputs/<run_name>/NT{4|6}/err-abs/{sym|notsym}/
- 例:
  - ./run_err_abs_for_run_name.sh --run-name 20260123_0300__nostage --seed-start 5 --seed-end 14 --stage 9 --output-name err_abs_stage9

### 学習コードの楽観的初期化（INIT_EV）
- 対象: `training/learning_ntuple_sym.cpp`, `training/learning_ntuple_notsym.cpp`
- 環境変数 `INIT_EV` を指定すると、タプル初期値がその値で初期化される
- 未指定の場合は従来通り 0
- 例:
  - `INIT_EV=1000 ./learning_ntuple_sym 5 20260123_0300__nostage`
  - `INIT_EV=1000 ./learning_ntuple_notsym 5 20260123_0300__nostage`


### run_graph_for_run_name.sh
- 目的: run_name 配下の board_data から任意グラフを生成（共通スクリプト）
- 必須引数:
  - --run-name NAME
  - --graph GRAPH（acc|err-rel|err-abs|surv|surv-diff|evals|scatter|scatter_v2|scatter-symdiff|acc-mean|acc-mean-symdiff|err-abs-mean|err-abs-mean-symdiff|err-rel-mean|err-rel-mean-symdiff|surv-mean|surv-mean-symdiff|surv-symdiff|evals-mean|evals-mean-symdiff）
- オプション:
  - --output-name NAME: 出力ファイルのベース名（デフォルト: graph名）
  - --ext EXT: 拡張子（デフォルト: png）
  - --seed-start N / --seed-end N: seed 範囲指定
  - --combine-seeds: 複数seedを1枚にまとめる
  - --stage N: meta.json の stage で絞り込み
  - --tuples LIST: 4,6 など
  - --sym-list LIST: sym,notsym など
  - --parallel N: 並列数（デフォルト: nproc）
- 出力先:
  - /HDD/momiyama2/data/study/analysis_outputs/<run_name>/NT{4|6}/{graph}/{sym|notsym}/
- 補足:
  - run_name の一致判定は「完全一致」に寄せています（`^<run_name>/(|$)`）。
  - 例: `__stage` を指定しても `__stage_g100` は混ざりません。
  - surv-diff 系は PP の `eval-after-state.txt` と対象 `state.txt` の progress 数が一致していない場合にエラーを返します。
- 例:
  - ./run_graph_for_run_name.sh --run-name 20260123_0300__nostage --graph acc --seed-start 5 --seed-end 14 --stage 9 --output-name acc_stage9
  - ./run_graph_for_run_name.sh --run-name 20260123_0300__nostage --graph acc-mean --seed-start 5 --seed-end 14 --stage 9 --output-name acc_mean_stage9
  - ./run_graph_for_run_name.sh --run-name 20260123_0300__nostage --graph acc-mean-symdiff --seed-start 5 --seed-end 14 --stage 9 --output-name acc_mean_symdiff_stage9

### run_acc_for_run_name.sh / run_err_rel_for_run_name.sh / run_surv_for_run_name.sh / run_surv_diff_for_run_name.sh / run_evals_for_run_name.sh
- 目的: run_graph_for_run_name.sh の薄いラッパー（graph 固定）
- 例:
  - ./run_acc_for_run_name.sh --run-name 20260123_0300__nostage --seed-start 5 --seed-end 14 --stage 9 --output-name acc_stage9
  - ./run_err_rel_for_run_name.sh --run-name 20260123_0300__nostage --seed-start 5 --seed-end 14 --stage 9 --output-name err_rel_stage9
  - ./run_surv_for_run_name.sh --run-name 20260123_0300__nostage --seed-start 5 --seed-end 14 --stage 9 --output-name surv_stage9
  - ./run_surv_diff_for_run_name.sh --run-name 20260123_0300__nostage --seed-start 5 --seed-end 14 --stage 9 --output-name surv_diff_stage9
  - ./run_evals_for_run_name.sh --run-name 20260123_0300__nostage --seed-start 5 --seed-end 14 --stage 9 --output-name evals_stage9


### clean_build_artifacts.sh
- 目的: board_data 関係の実行で生成されたバイナリ・ロックファイルを削除
- 削除対象:
  - Mini-2048-data-processing-main/NT/play_nt, play_nt_ns
  - Mini-2048-data-processing-main/perfect_player/eval_state_pp, eval_after_state_pp
  - Mini-2048-data-processing-main/graph/config.json.lock
- 例:
  - ./scripts/clean_build_artifacts.sh

## Mini-2048-data-processing-main/

### run_score_log_for_run_name.sh
- 目的: log_score.csv（traincount vs average_score）を読み込み、NT4/NT6・sym/notsym を重ねたグラフを作成
- 入力:
  - /HDD/momiyama2/data/study/ntuple_dat/<run_name>/seed<seed>/NT{4|6}_{sym|notsym}/log_score.csv
- 出力:
  - /HDD/momiyama2/data/study/analysis_outputs/<run_name>/score_log.png
- オプション:
  - --split-nt: NT4/NT6 を別図に分けて出力（score_log_NT4.png / score_log_NT6.png）
  - --output FILE: 出力ファイル名変更
  - --dat-root / --out-root: 入出力のルート変更
- 例:
  - ./run_score_log_for_run_name.sh --run-name 20260128_0600_OI1200__stage
  - ./run_score_log_for_run_name.sh --run-name 20260128_0600_OI1200__stage --split-nt

### run_scatter_for_run_name.sh
- 目的: uv graph を実行し、analysis_outputs に保存
- 出力先:
  - /HDD/momiyama2/data/study/analysis_outputs/<run_name>/NT{4|6}/{graph}/{sym|notsym}/
  - graph側の --output-dir を使って直接保存（output/ への移動は不要）
- デフォルト: seedごとに個別出力（複数seed指定時も分割）
  - まとめる場合は --combine-seeds を指定
- --parallel N で並列実行が可能
- 出力ファイル名は --output-name のベース名にプレイヤ名が付く（scatterの仕様）
  - 例: scatter_stage9_20260123_0300__stage__seed5__NT4_sym.png
- 例:
  - ./run_scatter_for_run_name.sh --run-name 20260123_0300__stage --seed-start 5 --seed-end 14 --stage 9 --output-name scatter_stage9 --parallel 8

### run_scatter_pipeline.sh
- 目的: meta.json 生成（不足分のみ）→ PP評価 → グラフ出力
- 前提: board_data に after-state.txt/eval.txt があること、perfect_player/db2.out があること
- 補足: PP出力は `--output-mode` により以下へ保存
  - per-nt: board_data/<run_name>/seedX/NT*_*/eval-state.txt, eval-after-state.txt
  - pp: board_data/PP/game_counts<game_count>/seed<seed>/eval-*-<safe_name>.txt

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
- 目的: board_data の state/after-state を PP で評価し、eval-state/after-state を作成
- 必須引数:
  - --run-name NAME
- オプション:
  - --board-root PATH: board_data ルート（省略時は ../board_data）
  - --output-mode MODE: per-nt（デフォルト）または pp
  - --force: 既存の eval-state/after-state を上書き
  - --parallel N: 並列数（デフォルト: nproc）
- 出力先:
  - per-nt: board_data/<run_name>/seedX/NT*_*/eval-state.txt, eval-after-state.txt
  - pp: board_data/PP/game_counts<game_count>/seed<seed>/eval-*-<safe_name>.txt
    - game_count は各NTディレクトリの meta.json から取得（無い場合はエラー）
- 例:
  - ./perfect_player/run_eval_pp_for_run_name.sh --run-name 20260123_0300__nostage
  - ./perfect_player/run_eval_pp_for_run_name.sh --run-name 20260123_0300__nostage --board-root /HDD/momiyama2/data/study/board_data --output-mode per-nt --force --parallel 4
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
- scatter は PP 評価ファイルが必要（per-nt または board_data/PP/game_counts*/seed*/）。

### run_train_nt4a_trainonly.sh
- 状態: 個別NT用（推奨: run_train_only.sh で tuples=4 + NT4a指定が必要な場合はこちら）
- 目的: NT4a (sym/notsym) の学習のみ実行（board_data/eval は作成しない）
- 4tuple のタプルセットは NT4a を使用（-DNT4A）
- 出力:
  - .dat: /HDD/momiyama2/data/study/ntuple_dat/<run_name>/seed<seed>/NT4_{sym|notsym}/
  - log: /HDD/momiyama2/data/study/training_logs/<run_name>/seed<seed>/NT4_{sym|notsym}/
- 主な指定:
  - --run-name-base, --seed-start/--seed-end or --seeds, --init-ev
  - --nostage で stage+nostage 両方実行
  - --parallel, --stdout-log
- run_name 衝突時の挙動:
  - 既存の NT4_sym/NT4_notsym が見つかると __nt4a を自動付与（--allow-collide で無効化）
- 例:
  - INIT_EV=1200 PARALLEL=16 RUN_NAME_BASE=20260124_1700_OI1200 \
    ./training/run_train_nt4a_trainonly.sh
