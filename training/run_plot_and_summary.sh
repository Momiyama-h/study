# ファイルが存在しない場合でも空リスト扱い
shopt -s nullglob
#!/usr/bin/env bash
set -euo pipefail

summary_file="score_summary.csv"
echo "seed,tuple,symmetry,timestamp,score" > "$summary_file"

OUTPUT_ROOT="mini2048_outputs"
SEEDS=("$@")  # コマンドライン引数で複数seed指定
TUPLES=(4 6)

# 実行時間（タイムスタンプ）を自動抽出
for SEED in "${SEEDS[@]}"; do
  for tuple in "${TUPLES[@]}"; do
    # sym側ファイルのみでペア処理・スコア抽出
    files=($(ls ${OUTPUT_ROOT}/log_${tuple}tuple_sym_seed${SEED}_*.txt 2>/dev/null))
    for file in "${files[@]}"; do
      ts=$(echo "$file" | sed -E 's/.*_seed[0-9]+_([0-9]{8}_[0-9]{4})\.txt/\1/')
      pair_file="${OUTPUT_ROOT}/log_${tuple}tuple_notsym_seed${SEED}_${ts}.txt"
      if [ -f "$pair_file" ]; then
        png="${OUTPUT_ROOT}/log_${tuple}tuples_seed${SEED}_${ts}.png"
        # plot_scores.pyの標準出力を取得
        output=$(python plot_scores.py --file1 "$file" --file2 "$pair_file" --output "$png")
        # sym側のfinal
        final_sym=$(echo "$output" | grep "log_${tuple}tuple_sym_seed${SEED}_${ts}:" | grep "final=" | awk -F'final=' '{print $2}' | awk '{print $1}')
        # notsym側のfinal
        final_notsym=$(echo "$output" | grep "log_${tuple}tuple_notsym_seed${SEED}_${ts}:" | grep "final=" | awk -F'final=' '{print $2}' | awk '{print $1}')
        # CSVに追記
        if [ -n "$final_sym" ]; then
          echo "${SEED},${tuple},sym,${ts},${final_sym}" >> "$summary_file"
        fi
        if [ -n "$final_notsym" ]; then
          echo "${SEED},${tuple},notsym,${ts},${final_notsym}" >> "$summary_file"
        fi
      fi
    done
  done
done

