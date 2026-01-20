# SETUP_SERVER.md

# Server / WSL Operating Notes (study)

目的：WSLで開発・pushし、サーバは pull → 実行に徹する。  
対象リポジトリ：`Momiyama-h/study.git`（branch: main）

---

## 1. 重要パス（サーバ）
- 作業ツリー（Git 管理）：`/HDD/momiyama2/repo`
- データ（Git 管理外）：
  - `STUDY_DATA_ROOT=/HDD/momiyama2/data/study`
  - `${STUDY_DATA_ROOT}/ntuple_dat/`（学習済み .dat）
  - `${STUDY_DATA_ROOT}/training_logs/`（学習ログ）
  - `${STUDY_DATA_ROOT}/board_data/<run_id>/`（state/after-state/eval/meta.json）
  - `${STUDY_DATA_ROOT}/analysis_outputs/<run_id>/`（分析結果）
- アーカイブ置き場：`/HDD/momiyama2/archives/`

初期作成（サーバ）：
```bash
mkdir -p /HDD/momiyama2/data/study/{ntuple_dat,training_logs,board_data,analysis_outputs}
mkdir -p /HDD/momiyama2/archives
```

repo との接続（サーバ）：
```bash
ln -s "/HDD/momiyama2/data/study/board_data" \
  /HDD/momiyama2/repo/Mini-2048-data-processing-main/board_data
ln -s "/HDD/momiyama2/data/study/analysis_outputs" \
  /HDD/momiyama2/repo/Mini-2048-data-processing-main/output
```

---

## 2. 重要パス（ローカル）
- 作業ツリー（Git 管理）：`/home/momiyama/work/mini2048-monorepo`
- データ（Git 管理外）：
  - `STUDY_DATA_ROOT=/home/momiyama/study-data`
  - `${STUDY_DATA_ROOT}/ntuple_dat/`（学習済み .dat）
  - `${STUDY_DATA_ROOT}/training_logs/`（学習ログ）
  - `${STUDY_DATA_ROOT}/board_data/<run_id>/`（state/after-state/eval/meta.json）
  - `${STUDY_DATA_ROOT}/analysis_outputs/<run_id>/`（分析結果）

初期作成（ローカル）：
```bash
mkdir -p /home/momiyama/study-data/{ntuple_dat,training_logs,board_data,analysis_outputs}
```

repo との接続（ローカル）：
```bash
ln -s "/home/momiyama/study-data/board_data" \
  /home/momiyama/work/mini2048-monorepo/Mini-2048-data-processing-main/board_data
ln -s "/home/momiyama/study-data/analysis_outputs" \
  /home/momiyama/work/mini2048-monorepo/Mini-2048-data-processing-main/output
```

---

## 3. 重要パス（DESKTOP04）
- 作業ツリー（Git 管理）：`<path>`
- データ（Git 管理外）：
  - `STUDY_DATA_ROOT=<path>`
  - `${STUDY_DATA_ROOT}/ntuple_dat/`（学習済み .dat）
  - `${STUDY_DATA_ROOT}/training_logs/`（学習ログ）
  - `${STUDY_DATA_ROOT}/board_data/<run_id>/`（state/after-state/eval/meta.json）
  - `${STUDY_DATA_ROOT}/analysis_outputs/<run_id>/`（分析結果）
- アーカイブ置き場：`<path>`

初期作成（DESKTOP04）：
```bash
mkdir -p <STUDY_DATA_ROOT>/{ntuple_dat,training_logs,board_data,analysis_outputs}
```

repo との接続（DESKTOP04）：
```bash
ln -s "<STUDY_DATA_ROOT>/board_data" \
  <repo_path>/Mini-2048-data-processing-main/board_data
ln -s "<STUDY_DATA_ROOT>/analysis_outputs" \
  <repo_path>/Mini-2048-data-processing-main/output
```
