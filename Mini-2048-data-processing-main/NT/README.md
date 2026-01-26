## 注意出力ファイルは全て board_data ディレクトリの下の各プレイヤーディレクトリの中に出力されます

## N タプルプレイヤーのプレイした情報が欲しい,N タプルプレイヤーを使ったグラフを書きたい場合

Play_NT_player.cpp を動かします

- state.txt (プレイ中に出てきた全ての state)
- after-state.txt (プレイ中に出てきた全ての aftar state)
- eval.txt (プレイ中に出てきた state から選択できた全ての afterstate の評価値一覧)
  この 3 種類のファイルが出てきます

# 動かしかた

```bash
g++ Play_NT_player.cpp -std=c++20
```

```bash
./a.out seed ゲーム数 評価ファイル
```

例:

```bash
./a.out 0 100 4tuple_data_9.dat
```

このように動かせば動きます。評価ファイルの先頭を参照してタプルを選んでいますので、評価ファイルの名前を変更する際は注意してください。

### SINGLE_STAGE（マルチステージ無効）で使う場合

学習側を `-DSINGLE_STAGE` でビルドした .dat を使う場合は、評価側も同じフラグでビルドしてください。

例:
```bash
g++ Play_NT_player.cpp -std=c++20 -DSINGLE_STAGE -o play_nt_ns
./play_nt_ns 0 100 6tuple_sym_data_0_0.dat sym 6
```

`eval_state.cpp` / `eval_after_state.cpp` を使う場合も同様に `-DSINGLE_STAGE` を付けます。

### board_data 世代分け（環境変数）

`BOARD_DATA_ROOT` を設定すると、出力先の `board_data` を任意のディレクトリに切り替えられます。
未設定の場合は従来通り `../board_data` に出力されます。

命名ルール（運用方針）:
- `YYYYMMDD_HHMM_{tuple}{sym}_seed{seed}_g{games}`
  例: `20260116_2145_6sym_seed0_g10000`

例:
```bash
BOARD_DATA_ROOT=../board_data/20260116_2145_6sym_seed0_g10000 ./a.out 0 100 6tuple_sym_data_0_0.dat sym 6
```

## 他のプレイヤーがプレイした state から N タプルプレイヤーが評価する場合

eval_state.cpp を動かします。

- eval-state-<safe_name>.txt (state から遷移可能な afterstate の評価値の一覧ファイル)
  このファイルが出てきます。

# 動かしかた

```bash
g++ eval_state.cpp -std=c++20
```

```bash
./a.out load-player-name EV-file
```

例:

```bash
./a.out PP 4tuple_data_9.dat
```

## 他のプレイヤーがプレイした afterstate を N タプルプレイヤーが評価する場合

eval_after_state.cpp を動かします。

- eval-after-state-PP.txt (after state の評価値の一覧ファイル,scatter を書くのに使う)

# 動かしかた

```bash
g++ eval_after_state.cpp -std=c++20
```

```bash
./a.out load-player-name EV-file
```

例:

```bash
./a.out PP 4tuple_data_9.dat
```
