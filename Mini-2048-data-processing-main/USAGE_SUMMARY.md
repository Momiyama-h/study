# Mini-2048-data-processing-main 使い方まとめ

主要な実行ファイル/スクリプトの使い方を簡潔に整理したメモです。
特記がない限り、例のパスはこのリポジトリ相対です。

## 共通メモ
- 多くのC++ツールは `../board_data` 配下に入出力します（実行ディレクトリ基準）。
- NT系は `BOARD_DATA_ROOT` で出力先ルートを上書き可能。
- `relocation truncated` が出る場合は `-mcmodel=large`（必要なら `-no-pie` も追加）。

## NT（Nタプルプレイヤ） - `NT/`

### Play_NT_player.cpp
コンパイル:
```
g++ Play_NT_player.cpp -O2 -std=c++20 -o play_nt
```
実行:
```
./play_nt <seed> <game_counts> <evfile> [sym|notsym] [4|6]
```
出力:
- `state.txt`, `after-state.txt`, `eval.txt`
- 出力先: `../board_data/NT{4|6}_{sym|notsym}/`（または `BOARD_DATA_ROOT` + そのサブディレクトリ）

補足:
- `sym|notsym` や `4|6` を省略すると `evfile` 名から推定します。

### Play_NT_player_notsym.cpp（旧版）
コンパイル:
```
g++ Play_NT_player_notsym.cpp -O2 -std=c++20 -o play_nt_notsym
```
実行:
```
./play_nt_notsym <seed> <game_counts> <evfile> [4|6]
```
補足:
- notsym専用。可能なら `Play_NT_player.cpp` を優先。

### eval_state.cpp
コンパイル:
```
g++ eval_state.cpp -O2 -std=c++20 -o eval_state
```
実行:
```
./eval_state <load-player-name> <EV-file> [sym|notsym] [4|6]
```
出力:
- `../board_data/eval-state-<load-player-name>.txt`

### eval_after_state.cpp
コンパイル:
```
g++ eval_after_state.cpp -O2 -std=c++20 -o eval_after_state
```
実行:
```
./eval_after_state <load-player-name> <EV-file> [sym|notsym] [4|6]
```
出力:
- `../board_data/eval-after-state-<load-player-name>.txt`

### play_evalafterstates.cpp
コンパイル:
```
g++ play_evalafterstates.cpp -O2 -std=c++20 -o play_evalafterstates
```
実行（stdinで9要素の盤面を入力）:
```
./play_evalafterstates <EV-file>
```
補足:
- 標準入力の9整数/行を読み、JSON風の評価値を出力します。
- デフォルトは `6tuples_sym.h` 前提。

## perfect_player - `perfect_player/`

### Play_perfect_player.cpp
コンパイル:
```
g++ Play_perfect_player.cpp -O2 -std=c++20 -mcmodel=large -o play_pp
```
実行:
```
./play_pp <seed> <game_counts>
```
出力:
- `../board_data/PP/state.txt`
- `../board_data/PP/after-state.txt`
- `../board_data/PP/eval.txt`

### eval_state.cpp
コンパイル:
```
g++ eval_state.cpp -O2 -std=c++20 -mcmodel=large -o eval_state_pp
```
実行:
```
./eval_state_pp <path_to_directory>
```
出力:
- `../board_data/PP/eval-state-<dir>.txt`

補足:
- `state.txt` そのものではなく「ディレクトリ」を渡します。

### eval_after_state.cpp
コンパイル:
```
g++ eval_after_state.cpp -O2 -std=c++20 -mcmodel=large -o eval_after_state_pp
```
実行:
```
./eval_after_state_pp <path_to_directory>
```
出力:
- `../board_data/PP/eval-after-state-<dir>.txt`

## graph - `graph/`

準備:
```
uv sync
```
実行:
```
uv run -m graph <graph_type> [--exclude ...] [--intersection ...] [--is-show]
```
例:
```
uv run -m graph scatter_v2 --intersection NT4_sym
uv run -m graph histgram --exclude sample
```
補足:
- `board_data` はリポジトリ直下を想定。
- `scatter` / `scatter_v2` は `board_data/PP/eval-after-state-<player>.txt` が必要。
- `scatter_v2` は `eval.txt` の各行で最大評価値を使います。

## Expectimax - `Expectimax/`

### play_expectimax.cpp
コンパイル:
```
g++ play_expectimax.cpp -O2 -std=c++20 -o play_expectimax
```
実行:
```
./play_expectimax <seed> <num_games> <depth> <EV-file>
```
補足:
- デフォルトは6タプルsym。4タプルは `-DNT4` で切り替え。

### Play_NT_player.cpp（Expectimax版）
コンパイル:
```
g++ Play_NT_player.cpp -O2 -std=c++20 -o play_exp_nt
```
実行:
```
./play_exp_nt <seed> <game_counts> <evfile> <depth>
```
出力:
- `../board_data/Exp_<depth>/<evfile-name>/state.txt` など

## mcts - `mcts/`

### mcts_NT.cpp
コンパイル:
```
g++ mcts_NT.cpp -O2 -std=c++20 -o mcts_nt
```
実行:
```
./mcts_nt <seed> <game_counts> <EV-file> <simulations> <randomTurn> <expand_count> <debug> <c> <Boltzmann> <expectimax>
```
出力:
- `../board_data/MCTS{4|6}/game_count...`（パラメータごとのネスト）

## NT_all_tuple - `NT_all_tuple/`

### play/*（greedy/mcts/expectimax/mini_*）
使用例（多くの play_* が共通）:
```
./play_greedy <seed> <game_counts> <evfile>
```
補足:
- `evfile` 名に `TupleNumber`/`Multistaging`/`OI`/`seed` などが埋め込み。
- 出力ディレクトリ例: `../board_data/NT<NT>_TN<TupleNumber>_OI<oi>_seed<seed>_normal/`
- タプルサイズは `-DT1` ... `-DT9` のコンパイル定義で切替。

### eval/eval_state.cpp
コンパイル:
```
g++ eval_state.cpp -O2 -std=c++20 -o eval_state_all
```
実行:
```
./eval_state_all <path_to_directory> <evfile>
```
補足:
- 圧縮/ gzip 読み込み対応。ファイル名からパラメータ取得。
- 出力は `../board_data/eval-state-<dir>.txt`。

### eval/eval_after_state.cpp
コンパイル:
```
g++ eval_after_state.cpp -O2 -std=c++20 -o eval_after_state_all
```
実行:
```
./eval_after_state_all <path_to_directory> <evfile>
```
出力:
- `../board_data/eval-after-state-<dir>.txt`

## Python（データ整理・可視化）

### perfect_player/process_all_directories.py
概要:
- `board_data` 配下の複数ディレクトリに対して `eval_state` / `eval_after_state` を一括実行します。
実行:
```
python3 perfect_player/process_all_directories.py '<pattern>'
```
例:
```
python3 perfect_player/process_all_directories.py '20260116_0419_*'
```
補足:
- `eval_state` / `eval_after_state` は事前に `perfect_player/` でビルド済みが前提です。

### average_score.py
概要:
- `after-state.txt` に含まれるスコアを集計（平均/中央値/標準偏差）。
実行:
```
python3 average_score.py '<pattern>' [表示件数]
```
例:
```
python3 average_score.py '20260116_0419_*' 10
```

### graph（可視化）
準備:
```
uv sync
```
実行:
```
uv run -m graph <graph_type> [--exclude ...] [--intersection ...] [--is-show]
```
例:
```
uv run -m graph scatter_v2 --intersection NT4_sym
uv run -m graph histgram --exclude sample
```
補足:
- `board_data` はリポジトリ直下を想定します。
- `scatter` / `scatter_v2` は `board_data/PP/eval-after-state-<player>.txt` が必要です。

### mcts/analyze_scores.py
概要:
- MCTSのパラメータごとのスコア集計と相関分析。
実行:
```
python3 mcts/analyze_scores.py <board_dataのサブディレクトリ>
```
例:
```
python3 mcts/analyze_scores.py MCTS6
```
