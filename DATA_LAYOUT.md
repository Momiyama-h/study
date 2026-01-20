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

## run_id 規約（推奨）
run 1回につきディレクトリ1つを作る。

例:
- `20260120_1805_NT6_sym_seed9_g10000`
- `20260120_1810_PP_seed1`

生成例:
```bash
RUN_ID="$(date +%Y%m%d_%H%M%S)_exp1"
mkdir -p "${STUDY_DATA_ROOT}/board_data/${RUN_ID}"
mkdir -p "${STUDY_DATA_ROOT}/analysis_outputs/${RUN_ID}"
echo "$RUN_ID"
```

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
- 学習・分析で同一の `run_id` を使うことを推奨（追跡・再現性のため）
- 分析が学習の派生である場合は `run_id` を継承し、必要なら suffix を追加する  
  例: `20260120_1805_NT6_sym_seed9_g10000__scatter`

## ローカル環境のデータ配置（推奨）
- STUDY_DATA_ROOT=$HOME/study-data
- 以下の構成を推奨
  - ${STUDY_DATA_ROOT}/ntuple_dat/  : 学習済み .dat
  - ${STUDY_DATA_ROOT}/training_logs/  : 学習ログ
  - ${STUDY_DATA_ROOT}/board_data/<run_id>/     : state/after-state/eval/meta.json などの分析入力
  - ${STUDY_DATA_ROOT}/analysis_outputs/<run_id>/ : 図・集計CSVなどの分析結果

repo 側は symlink で接続する。

```bash
ln -s "${STUDY_DATA_ROOT}/board_data"   Mini-2048-data-processing-main/board_data
ln -s "${STUDY_DATA_ROOT}/analysis_outputs"   Mini-2048-data-processing-main/output
```

## 保存先一覧（要点）
| データ | 保存先 |
| --- | --- |
| 学習済みNタプル (.dat) | ${STUDY_DATA_ROOT}/ntuple_dat/ |
| 学習ログ | ${STUDY_DATA_ROOT}/training_logs/ |
| state/after-state/eval | ${STUDY_DATA_ROOT}/board_data/<run_id>/ |
| meta.json | ${STUDY_DATA_ROOT}/board_data/<run_id>/ |
| 図・集計CSV | ${STUDY_DATA_ROOT}/analysis_outputs/<run_id>/ |

