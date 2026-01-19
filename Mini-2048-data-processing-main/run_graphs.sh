#!/bin/bash

# 動的に変更する部分
INTERSECTION="6tuples_single/6tuple_data_9.dat 6tuples_single/6tuple_data_9.dat_single"
OutputDir="NT6"

# 各コマンドを実行
uv run -m graph acc --intersection $INTERSECTION
uv run -m graph err-abs --intersection $INTERSECTION
uv run -m graph err-rel --intersection $INTERSECTION
uv run -m graph surv --intersection $INTERSECTION

# 出力結果を保存
mkdir -p output/$OutputDir
mv output/*.pdf output/$OutputDir