## 注意

- スタック領域を大量に消費するのでメモリ 16G 以上の Linux 環境で動かしてください
- 出力ファイルは全て board_data ディレクトリの下の各プレイヤーディレクトリの中に出力されます
- `run_eval_pp_for_run_name.sh` の `--output-mode` で出力先を切り替えられます
  - デフォルトは `per-nt`（`board_data/<run_name>/seed<seed>/NT*_*` 直下に `eval-state.txt` と `eval-after-state.txt`）
  - `pp` を指定すると従来通り `board_data/PP/` に安全名で出力します

## N タプルプレイヤーのプレイした情報が欲しい,N タプルプレイヤーを使ったグラフを書きたい場合

Play_PP_player.cpp を動かします

- state.txt (プレイ中に出てきた全ての state)
- after-state.txt (プレイ中に出てきた全ての aftar state)
- eval.txt (プレイ中に出てきた state から選択できた全ての afterstate の評価値一覧)
  この 3 種類のファイルが出てきます

# 動かしかた

```bash
g++ Play_perfect_player.cpp -std=c++20 -mcmodel=large
```

```bash
./a.out seed ゲーム数
```

例:

```bash
./a.out 0 100
```

## 他のプレイヤーがプレイした state から N タプルプレイヤーが評価する場合

eval_state.cpp を動かします。

- eval-state-<safe_name>.txt (state から遷移可能な afterstate の評価値の一覧ファイル)
  このファイルが出てきます。

# 動かしかた

```bash
g++ eval_state.cpp -std=c++20 -mcmodel=large
```

```bash
./a.out <path_relative_to_board_data>
```

例:

```bash
./a.out 20260116_0419_4sym_seed5_g100/NT4_sym
```

出力ファイル名は、`/` を `__` に置換した安全名で保存されます。
例: `eval-state-20260116_0419_4sym_seed5_g100__NT4_sym.txt`

## 他のプレイヤーがプレイした afterstate を N タプルプレイヤーが評価する場合

eval_after_state.cpp を動かします。

- eval-after-state-<safe_name>.txt (after state の評価値の一覧ファイル,scatter を書くのに使う)

# 動かしかた

```bash
g++ eval_after_state.cpp -std=c++20 -mcmodel=large
```

```bash
./a.out <path_relative_to_board_data>
```

例:

```bash
./a.out 20260116_0419_4sym_seed5_g100/NT4_sym
```

出力ファイル名は、`/` を `__` に置換した安全名で保存されます。
例: `eval-after-state-20260116_0419_4sym_seed5_g100__NT4_sym.txt`
