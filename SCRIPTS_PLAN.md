# 統一スクリプト計画（案）

## 目的
  起動方法・出力規約・保守対象を明確化する。
- 既存スクリプトは当面温存し、段階的に置換する。

---

## 統一対象（単体スクリプト）

### 1) training/run_train_unified.sh
- **用途**: 学習のみ（board_data/eval は作成しない）
- **内部呼び出し**:
  - `run_train_4patterns_10seeds_trainonly.sh`（NT4/NT6）
  - `run_train_nt5a_trainonly.sh`（NT5a）

**決定ルール**
- `--tuples` / `TUPLES` に基づいて実行対象を選ぶ
  - 4/6 → NT4/NT6
  - 5 → NT5a（nostage-only は不可）
- `--stage-mode` で stage/nostage/both を決定
- `--seed-start/--seed-end` または `--seeds` で seed 範囲を決定
- `--policy` で Greedy / Expectimax を決定（`greedy` / `expecti3`）
- run_name は `RUN_NAME_BASE + __stage / __nostage`（Expectimax の場合は `__policy=expecti3` を付与）

**出力**
- .dat:
  - `/HDD/momiyama2/data/study/ntuple_dat/<run_name>/seed<seed>/NT{4|5|6}_{sym|notsym}/`
- log:
  - `/HDD/momiyama2/data/study/training_logs/<run_name>/seed<seed>/NT{4|5|6}_{sym|notsym}/`

---

## 将来の統一方針

### 段階的移行
1. **現行は単体優先で運用**
2. **旧スクリプトに「非推奨」ラベルを追加**（済）
3. **一定期間後、旧スクリプトを縮小 or 廃止**

### 旧スクリプト（候補）
- `run_train_4patterns_10seeds_trainonly.sh`
- `run_train_eval_4patterns_10seeds_nostage.sh`
- `run_train_eval_4patterns_10seeds_stagecompare.sh`
- `run_train_eval_4patterns_5seeds.sh`
- `run_train_nt4a_trainonly.sh`
- `run_train_nt4b_notsym_only.sh`
- `run_train_nt5a_trainonly.sh`

---

## 機能が被るスクリプト一覧（現状の整理）

### 学習実行（学習のみ）
- `run_train_unified.sh`
- `run_train_only.sh`
- `run_train_4patterns_10seeds_trainonly.sh`
- `run_train_nt4a_trainonly.sh`
- `run_train_nt5a_trainonly.sh`

### グラフ生成（board_data 由来）
- `Mini-2048-data-processing-main/graph`（`python3 -m graph`）
  - 追加: `err-mae`, `err-mae-mean`, `err-mae-symdiff`, `err-mae-mean-symdiff`
  - 依存: `eval.txt` + `pp-eval-state.txt`（各 seed/NT/eval_seed ディレクトリ直下）

### 学習ログから平均/推移を作る
- `plot_score_log_mean.py` / `run_plot_score_log_mean.sh`
  - 学習中の `log_score_*.csv` を集計し、update/cpu 軸の平均推移を出力
- `plot_learning_curves.py`（別実装）
  - 旧形式や別可視化（用途が被る場合は段階的に整理）

### 既存 .dat / .txt から平均を作る（CSV）
- `make_seed_score_matrix.py`（board_data or dat）
- `run_eval_scores_from_dat.sh`（dat を再プレイ）
- `export_score_averages.py` / `run_export_score_averages_for_run_name.sh`（学習ログ）

### 生存率差分（seed構造の統計）
- `Mini-2048-data-processing-main/analysis/make_survival_diff_stats.py`
  - sym/notsym の survival curve 差分を train_seed 単位で集計
  - 出力: surv_diff_by_train_seed_long.csv / surv_diff_summary.csv / surv_diff_auc.csv
  - 図: surv_diff_curve_NT*.{png|pdf}, surv_diff_auc_NT*.{png|pdf}

### グラフ生成（training_logs 由来）
- `run_plot_scores_for_run_name.sh`
  - `training_logs/<run>/seed*/NT*_*/log_*tuple_*_seed*.txt` から sym/notsym 比較を作図

---

## 出力ルールの統一（今後）
- run_name は原則 `RUN_NAME_BASE + __{stage|nostage}`
- seed 範囲は run_name に埋め込まず、引数で管理する
- dat / log / board_data のディレクトリ構造は固定

---

## 未対応・拡張予定
- NT5a の **nostage-only** 対応は未定
- stage/nostage を **1回の実行で混在させない** 安全運用を推奨
- オプション追加が必要なら単体に集約する

---

## PP評価/相関まわりの変更メモ（今後の課題）

### 変更すべき点
1. **PP評価 exe の board_root 固定**
   - `eval_state.cpp / eval_after_state.cpp` が `../board_data` 固定。
   - `run_eval_pp_for_run_name.sh --board-root` が実質無効になり得る。
   - → **board_root を引数 or 環境変数で渡せるようにする**のが必要。
2. **PP評価の出力先の一貫性**
   - 原則 **各 `seed/NT*_*/` 直下に `pp-eval-*.txt`** を置く運用。
   - board_root ズレで別場所に出力されるリスクあり。
3. **meta.json の `game_count` 欠落**
   - structured path 解決に必要。欠落で PP 評価ファイルが見つからなくなる。
   - → **meta.json に `game_count` を必須化**する。
4. **命名の整合**
   - `pp-eval-state.txt` の中身が “after-stateの4手評価” のため誤解要因。
   - 互換優先なら据え置き、将来は整理推奨。

### make_pp_corr_matrix.py 入出力の再検討
**入力（優先順）**
1. `seed/NT*_*/pp-eval-after-state.txt`（基本）
2. `seed/NT*_*/eval-after-state.txt`（PP評価が同居の場合）
3. `board_data/PP/game_counts{N}/seed{S}/eval-after-state-<safe_name>.txt`（fallback）
4. `board_data/PP/eval-after-state-<safe_name>.txt`（旧式）

**出力**
- 既定: `analysis_outputs/<run_name>/pp_corr/pp_corr_spearman_after.csv`
- 併記推奨: `pp_corr_spearman_state.csv`（eval-state版）
- README で条件（seed/tuple/sym/game_count）を明文化すると査読向けに強い。

---

## eval_seed層導入時の影響対象チェックリスト

### 解析スクリプト（state/after-state直下前提）
- training/make_progress_counts.py
- training/make_seed_score_matrix.py
- training/make_pp_corr_matrix.py
- Mini-2048-data-processing-main/make_tile_prob_by_nt_sym.py
- Mini-2048-data-processing-main/make_pp_regression_matrix.py
- Mini-2048-data-processing-main/average_progress.py
- Mini-2048-data-processing-main/average_score.py
- Mini-2048-data-processing-main/run_scatter_pipeline.sh
- Mini-2048-data-processing-main/perfect_player/process_all_directories.py
- Mini-2048-data-processing-main/graph/common.py
- Mini-2048-data-processing-main/graph/survival.py
- Mini-2048-data-processing-main/graph/survival_diff.py

### プレイヤー/評価系（state/after-stateの入出力）
- Mini-2048-data-processing-main/NT/Play_NT_player.cpp
- Mini-2048-data-processing-main/NT/Play_NT_player_notsym.cpp
- Mini-2048-data-processing-main/Expectimax/Play_NT_player.cpp
- Mini-2048-data-processing-main/mcts/mcts_NT.cpp
- Mini-2048-data-processing-main/NT_all_tuple/play/play_greedy*.cpp
- Mini-2048-data-processing-main/NT_all_tuple/play/play_expectimax.cpp
- Mini-2048-data-processing-main/NT_all_tuple/play/play_mcts.cpp

### eval/PP 生成
- Mini-2048-data-processing-main/NT/eval_state.cpp
- Mini-2048-data-processing-main/NT/eval_after_state.cpp
- Mini-2048-data-processing-main/NT_all_tuple/eval/eval_state.cpp
- Mini-2048-data-processing-main/NT_all_tuple/eval/eval_after_state.cpp
- Mini-2048-data-processing-main/perfect_player/eval_state.cpp
- Mini-2048-data-processing-main/perfect_player/eval_after_state.cpp
- Mini-2048-data-processing-main/perfect_player/run_eval_pp_for_run_name.sh

### ドキュメント（パス前提の明記が必要）
- DATA_LAYOUT.md
- SHELL_SCRIPTS_GUIDE.md
- SCRIPTS_PLAN.md
- Mini-2048-data-processing-main/USAGE_SUMMARY.md
- Mini-2048-data-processing-main/graph/README.md
- Mini-2048-data-processing-main/NT/README.md
- Mini-2048-data-processing-main/perfect_player/README.md

### メモ
- eval層（例: eval000）を挟むだけだと、上記の多くが探索失敗する。
- 互換symlink方式を使うなら修正範囲は大幅に減らせる。
