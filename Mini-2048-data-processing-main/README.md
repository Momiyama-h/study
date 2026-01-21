# Mini-2048-data-processing

## python 注意点

uv を用いて python のライブラリの管理を行っています。
詳しい内容は[この README](./graph/README.md)を確認してください。

## perfect_player 注意点

perfect_player はメモリ不足が懸念されるので、サーバで動かしてください。
それ以外の環境の場合動作の保証はしません。
詳しい内容は[この README](./perfect_player/README.md)を確認してください。

## NT 注意点

4tuple_data_9.dat のような各タプルの学習済みファイルが必要です。
詳しい内容は[この README](./NT/README.md)を確認してください。

## 一括実行（scatter）

`run_scatter_pipeline.sh` で、以下を一括実行できます。
- meta.json の不足分作成
- PP eval-after-state の不足分作成
- scatter の実行

例:
```bash
./run_scatter_pipeline.sh --seed-start 5 --seed-end 14 --tuples 4,6 --stage 9 --output scatter.png
```

補足:
- `--sync` を付けると `uv sync` を実行します
- `perfect_player/db2.out` が必要です

## TODO

- [x] グラフプロット用コードを記述する。

  - [x] accuracy
  - [x] error-relative
  - [x] error-absolute
  - [x] survival-rate
  - [x] scatter

- [x] グラフプロット用コードをマージする。

  - [x] `__main__.py`を完成させる。
  - [x] 各コードでプロットできるようにする。

- [x] 他の player の state を Perfect Player に食わせて、eval を出力するコードを記述する。(PP/eval*state*[player].txt)
- [x] 他の player の afterstate を Perfect Player に食わせて、eval を出力するコードを記述する。 (PP/eval*saftertate*[player].txt)
- [x] PP の surv を出そうとすると面倒
- [ ] surv diff を出せるようにしたい
- [ ] ディレクトリの中のデータを参照したいけど要検討
