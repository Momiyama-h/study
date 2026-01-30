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
- run_name は `RUN_NAME_BASE + __stage / __nostage`

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

## 出力ルールの統一（今後）
- run_name は原則 `RUN_NAME_BASE + __{stage|nostage}`
- seed 範囲は run_name に埋め込まず、引数で管理する
- dat / log / board_data のディレクトリ構造は固定

---

## 未対応・拡張予定
- NT5a の **nostage-only** 対応は未定
- stage/nostage を **1回の実行で混在させない** 安全運用を推奨
- オプション追加が必要なら単体に集約する
