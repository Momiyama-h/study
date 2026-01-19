## 注意

- スタック領域を大量に消費するのでメモリ 16G 以上の Linux 環境で動かしてください
- 出力ファイルは全て board_data ディレクトリの下の各プレイヤーディレクトリの中に出力されます

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

- eval-state-NT4.txt (state から遷移可能な afterstate の評価値の一覧ファイル)
  このファイルが出てきます。

# 動かしかた

```bash
g++ eval_state.cpp -std=c++20 -mcmodel=large
```

```bash
./a.out load-player-name
```

例:

```bash
./a.out NT4
```

## 他のプレイヤーがプレイした afterstate を N タプルプレイヤーが評価する場合

eval_after_state.cpp を動かします。

- eval-after-state-NT4.txt (after state の評価値の一覧ファイル,scatter を書くのに使う)

# 動かしかた

```bash
g++ eval_after_state.cpp -std=c++20 -mcmodel=large
```

```bash
./a.out load-player-name
```

例:

```bash
./a.out NT4
```
