# Graph
このプロジェクトは、2048のプレイヤデータを可視化するためのツールです。

## ドキュメント

### PlayerDataクラス

#### フィールド

| フィールド名 | 説明 |
|------------|------|
| `name` | プレイヤの名前（board_data相対パスの安全名） |
| `target_dir` | プレイヤのデータが格納されているディレクトリ |
| `pp_dir` | プレイヤのPPデータが格納されているディレクトリ |

#### プロパティ

| プロパティ名 | 説明 |
|------------|------|
| `state_file` | プレイヤのstateファイルのパス |
| `eval_file` | プレイヤの評価値ファイルのパス |
| `pp_eval_state` | プレイヤのプレイで現れたstateをPPに評価させた評価値ファイルのパス |
| `pp_eval_after_state` | プレイヤのプレイで現れたafter_stateをPPに評価させた評価値ファイルのパス |

#### meta.json (任意)

各データディレクトリに `meta.json` がある場合、seedやstageのフィルタに利用できます。

例:
```json
{
  "id": "20260116_0419_4sym_seed5_g100__NT4_sym",
  "relpath": "20260116_0419_4sym_seed5_g100/NT4_sym",
  "tuple": 4,
  "sym": "sym",
  "seed": 5,
  "stage": 9,
  "evfile": "4tuple_sym_data_5_9.dat"
}
```

補足: グラフ表示ラベルは config.json の label を使用し、未設定の場合は meta.json から
`NT{tuple}_{sym}_s{seed}_st{stage}` を自動生成します。

### common.py

#### データクラス

##### EvalAndHandProgress

評価値とゲーム進行度を格納するデータクラスです。

| フィールド | 型 | 説明 |
|-----------|-----|-----|
| `evals` | `list[float]` | 長さ4のリスト。4方向（上右下左）への評価値 |
| `prg` | `int` | ゲームの進行度（progress） |

###### プロパティ

| プロパティ名 | 戻り値 | 説明 |
|------------|-------|------|
| `idx` | `list[int]` | `evals`の中で最大値を持つインデックスのリスト |

##### PlotData

プロット用のデータを格納するデータクラスです。

| フィールド | 型 | 説明 |
|-----------|-----|-----|
| `x_label` | `str` | X軸のラベル |
| `y_label` | `str` | Y軸のラベル |
| `data` | `dict[str, GraphData]` | プレイヤー名をキーとするGraphDataの辞書 |

##### GraphData

グラフデータを格納するデータクラスです。

| フィールド | 型 | 説明 |
|-----------|-----|-----|
| `x` | `list[float]` | X軸の値のリスト |
| `y` | `list[float]` | Y軸の値のリスト |

#### 関数

##### get_eval_and_hand_progress

```python
def get_eval_and_hand_progress(eval_file: Path) -> list[EvalAndHandProgress]
```

評価値ファイルから評価値、選択した手、進行度を取得します。

| 引数 | 型 | 説明 |
|-----|-----|-----|
| `eval_file` | `Path` | 評価値ファイルのパス |

**戻り値**: `EvalAndHandProgress`のリスト

##### moving_average

```python
def moving_average(data, window_size)
```

移動平均を計算します。

| 引数 | 型 | 説明 |
|-----|-----|-----|
| `data` | `list[float]` or `numpy.ndarray` | 移動平均を計算するデータ |
| `window_size` | `int` | 移動平均の窓サイズ |

**戻り値**: 移動平均が計算された`numpy.ndarray`

## 導入

1. [uv](https://docs.astral.sh/uv/getting-started/installation/)をインストール。
2. `uv sync`を実行。ライブラリがインストールされる。

## 実行

`uv run -m graph [graph_type]`を実行。指定したグラフがプロットされる。

## グラフの種類

| グラフタイプ | 説明 |
|------------|------|
| `acc` | 正確性 |
| `acc-diff` | 正確性差分 |
| `err-rel` | 相対誤差 |
| `err-abs` | 絶対誤差 |
| `surv` | 生存率 |
| `surv-diff` | 生存率(パーフェクトプレイヤとの差) |
| `scatter` | パーフェクトプレイヤとの散布図 |
| `scatter_v2` | パーフェクトプレイヤとの散布図（eval最大値） |
| `histgram` | 得点分布 |
| `evals` | 評価値のProgressごとの散布図 |
| `boxplot-eval` | 評価値比率の箱ひげ図 |
| `pea` | progress評価と正確性の関係 |

補足: scatter は 1000 件、scatter_v2 は 1500 件をランダム抽出します。データ数が不足するとエラーになります。

## 引数の説明

### graph_type (必須)

グラフの種類を指定する。上記のグラフの種類から選択。

### --exclude

プロットを行う際に除外するプレイヤを指定する。複数指定可能。

**例**: NT4プレイヤを除外する場合
```
--exclude NT4
```

### --intersection

プロットを行う際に含めるプレイヤを指定する。複数指定可能。
指定しない場合は全てのプレイヤをプロットする。

**例**: NT4プレイヤとNT6プレイヤのみをプロットする場合
```
--intersection NT4 NT6
```

### --help, -h

コマンドのヘルプを表示する。

### --is-show

完成したグラフを表示する。

### --acc-diff-order

`acc-diff` の比較順を指定する。デフォルトは入力順。
選択肢: `input` / `sym-notsym` / `notsym-sym`

### --recursive

`board_data` 配下を再帰的に探索してデータを拾う。
PP評価ファイルは `board_data/PP/eval-after-state-<safe_name>.txt` だけでなく、
`board_data/<run_name>/seed<seed>/NT*_*` 直下の `eval-after-state.txt` も参照できる。

### --seed / --stage / --tuple / --sym

`meta.json` の値で絞り込む。

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

## 今後の予定

上から順に優先度が高い。

- [x] サブディレクトリ内のデータを参照できるようにする（--recursive）。
- [x] surv diff を出せるようにする。
- [ ] グラフ設定を行えるようにする。
- [ ] ファイル指定を tkinter でグラフィカルに行えるようにする。
