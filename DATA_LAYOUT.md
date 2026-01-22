# DATA_LAYOUT.md

# Data Layout and Execution Conventions (study)

このドキュメントは、`Momiyama-h/study.git` の **コード管理（Git）** と **実験データ管理（Git管理外）** を分離し、学習 (`training/`) と分析 (`Mini-2048-data-processing-main/`) を安全に運用するための規約をまとめたものです。

## リポジトリ概要
- GitHub: `git@github.com:Momiyama-h/study.git`（branch: `main`）
- 構成:
  - `training/`  
    学習コード（C++/Python 混在）。学習結果として `.dat` が溜まる想定。
  - `Mini-2048-data-processing-main/`  
    分析コード（C++/Python 混在）。**uv を使用**。入力は `training/` が生成した `.dat` 等。

## 運用方針（重要）
- **コードは Git 管理**（repo 配下）
- **実験データ・ログ・生成物は Git 管理しない**（HDD 側の固定データ領域へ）
- 学習と分析のコード依存は持たず、依存は **「データフロー（training → dat → analysis）」のみ**とする

## .dat 命名規則（決定）
学習済みNタプルのファイル名は以下の規則に従う。

```
*tuple_{sym|notsym}_data_{seed}_{stage}.dat
```

例:
- `4tuple_sym_data_5_9.dat`
- `6tuple_notsym_data_14_9.dat`

この命名規則は分析側の `meta.json` 生成や seed/stage の抽出に使う。

---

## SINGLE_STAGE（マルチステージ無効）運用
- 学習・評価を **1ステージ固定** にする場合は、学習/評価バイナリのコンパイル時に `-DSINGLE_STAGE` を付ける。
- seed5〜14、4/6タプルの nostage 用一括スクリプトは `training/run_train_eval_4patterns_10seeds_nostage.sh`。
- .dat の保存先は **run_name/seed/NT*_* の階層**で区別する（後述）。
- `board_data` は `run_name` で識別し、`__nostage` などの suffix を付けると追跡しやすい。

## 学習済みNタプル (.dat) の配置（新ルール）
学習時に `<run_name>` を指定し、以下の階層に自動保存する。

```
${STUDY_DATA_ROOT}/ntuple_dat/<run_name>/seed<seed>/{NT4_sym|NT4_notsym|NT6_sym|NT6_notsym}/
```

例:
- `${STUDY_DATA_ROOT}/ntuple_dat/20250201_1200__stage/seed15/NT6_sym/6tuple_sym_data_15_9.dat`
- `${STUDY_DATA_ROOT}/ntuple_dat/20250201_1200__nostage/seed15/NT6_notsym/6tuple_notsym_data_15_9.dat`

## 学習ログ (log_*.txt) の配置（新ルール）
`<run_name>` を .dat と共有し、以下の階層に保存する。

```
${STUDY_DATA_ROOT}/training_logs/<run_name>/seed<seed>/{NT4_sym|NT4_notsym|NT6_sym|NT6_notsym}/
```

例:
- `${STUDY_DATA_ROOT}/training_logs/20250201_1200__stage/seed15/NT6_sym/log_6tuple_sym_seed15_20250201_1200__stage.txt`
- `${STUDY_DATA_ROOT}/training_logs/20250201_1200__nostage/seed15/NT6_notsym/log_6tuple_notsym_seed15_20250201_1200__nostage.txt`

## データ保存の基準パス（サーバ推奨）
データのルート（推奨）:
- `STUDY_DATA_ROOT=/HDD/momiyama2/data/study`

サブ構造（推奨）:
- `${STUDY_DATA_ROOT}/ntuple_dat/`  
  学習済み .dat を集約して保存
- `${STUDY_DATA_ROOT}/training_logs/`  
  学習ログを集約して保存
- `${STUDY_DATA_ROOT}/analysis_outputs/<run_id>/`  
  分析結果（集計 CSV、加工済みデータ、図など）を run 単位で保存
- `${STUDY_DATA_ROOT}/board_data/`  
  分析用の入力データ（state/after-state/eval など）を保存
- `/HDD/momiyama2/archives/`  
  送付・退避用の圧縮ファイル（.tar.gz 等）置き場

> 注: 上記は推奨。環境により変更する場合は `STUDY_DATA_ROOT` を必ず指定する。

---

## board_data の配置（新ルール）
board_data は `<run_name>` と seed を明示した階層で保存する。

```
${STUDY_DATA_ROOT}/board_data/<run_name>/seed<seed>/{NT4_sym|NT4_notsym|NT6_sym|NT6_notsym}/
```

例:
- `${STUDY_DATA_ROOT}/board_data/20250201_1200__stage/seed15/NT6_sym/state.txt`
- `${STUDY_DATA_ROOT}/board_data/20250201_1200__nostage/seed15/NT6_notsym/eval.txt`

## repo との連携（推奨）
分析コードは `Mini-2048-data-processing-main/board_data` を参照するため、
サーバ運用では `STUDY_DATA_ROOT` 側の実データへシンボリックリンクで接続する。

例:
```bash
ln -s "${STUDY_DATA_ROOT}/board_data" \
  Mini-2048-data-processing-main/board_data
ln -s "${STUDY_DATA_ROOT}/analysis_outputs" \
  Mini-2048-data-processing-main/output
```

## run_id の対応
- 学習の `run_name` と分析の `run_id` を合わせると追跡が容易
- 分析が学習の派生である場合は `run_id` を継承し、必要なら suffix を追加する  
  例: `20250201_1200__stage__scatter`

## ローカル環境のデータ配置（推奨）
- STUDY_DATA_ROOT=$HOME/study-data
- 以下の構成を推奨
  - ${STUDY_DATA_ROOT}/ntuple_dat/  : 学習済み .dat
  - ${STUDY_DATA_ROOT}/training_logs/  : 学習ログ
  - ${STUDY_DATA_ROOT}/board_data/<run_name>/seed<seed>/NT*_*/ : state/after-state/eval/meta.json などの分析入力
  - ${STUDY_DATA_ROOT}/analysis_outputs/<run_id>/ : 図・集計CSVなどの分析結果

repo 側は symlink で接続する。

```bash
ln -s "${STUDY_DATA_ROOT}/board_data"   Mini-2048-data-processing-main/board_data
ln -s "${STUDY_DATA_ROOT}/analysis_outputs"   Mini-2048-data-processing-main/output
```

## 保存先一覧（要点）
| データ | 保存先 |
| --- | --- |
| 学習済みNタプル (.dat) | ${STUDY_DATA_ROOT}/ntuple_dat/<run_name>/seed<seed>/NT*_*/ |
| 学習ログ | ${STUDY_DATA_ROOT}/training_logs/ |
| state/after-state/eval | ${STUDY_DATA_ROOT}/board_data/<run_name>/seed<seed>/NT*_*/ |
| meta.json | ${STUDY_DATA_ROOT}/board_data/<run_name>/seed<seed>/NT*_*/ |
| 図・集計CSV | ${STUDY_DATA_ROOT}/analysis_outputs/<run_id>/ |
