mini2048コード疑問点
-TC関数部分
--論文の説明によるとdiff*((err[s][i][index])/aerrs[s][i][index])になりそうなところなぜかfabsで浮動小数点絶対値とってる
‐-非対称の方を8つとって平均をとる
‐‐

ログ・ファイル命名メモ
- prev: *nosym*.dat -> *notsym*.dat（既存 .dat をリネーム済み）
- prev: *nosym*.txt -> *notsym*.txt（既存 .txt をリネーム & 内容置換済み）

今後の運用方針（2026-02-17）
- 比較を簡単にするため、対称性ファミリは `run_name` 側で分ける
  - 例: `20260217_OI1200_rot180__stage`, `20260217_OI1200_diag__stage`
- 各 run の中の条件名は従来どおり `sym` / `notsym` を使う
  - 例: `seed7/NT4_sym`, `seed7/NT4_notsym`
- `meta.json` には実際の対称性ファミリ（`sym_family=rot180/diag/...`）を残す
- これにより既存の `sym vs notsym` 分析スクリプト（delta-box, delta-nt 等）を変換なしで再利用できる
