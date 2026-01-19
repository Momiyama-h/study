#!/bin/bash

# 最大同時実行プロセス数
max_jobs=32

# プロセス管理用
joblist=()

# 固定設定
seeds=(0 1 2 3 4 5 6 7 8 9) # seed の配列
game=100
tuple=(6)
simu=(750 1500 3000 6000 12000 15000 24000 48000 55000)
debug=0
randamTrun=(0 1)
expand_count=(1)

# 可変パラメータ
c_values=(-1)
boltzmann_values=(0)
expectimax_values=(1)

# データファイル
data_file_prefix="tuple_data_9.dat"

# 実行ファイル
executable="mcts_NT"

# 出力フォルダ
output_dir="results"
mkdir -p $output_dir

# プロセス監視関数
wait_for_jobs() {
    while [ "${#joblist[@]}" -ge "$max_jobs" ]; do
        for i in "${!joblist[@]}"; do
            if ! kill -0 "${joblist[i]}" 2>/dev/null; then
                unset 'joblist[i]'
            fi
        done
        joblist=("${joblist[@]}") # 配列を再構築してインデックスを詰める
        sleep 0.1
    done
}

echo "Compiling mcts_NT.cpp..."
c++ mcts_NT.cpp -std=c++20 -DNT4 -O2 -o mcts_NT4 || {
    echo "Failed to compile mcts_NT4"
    exit 1
}
c++ mcts_NT.cpp -std=c++20 -DNT6 -O2 -o mcts_NT6 || {
    echo "Failed to compile mcts_NT6"
    exit 1
}

# 実行ループ
for seed in "${seeds[@]}"; do
    for tuple_value in "${tuple[@]}"; do
        for c in "${c_values[@]}"; do
            for boltzmann in "${boltzmann_values[@]}"; do
                for expectimax in "${expectimax_values[@]}"; do
                    for depth in "${simu[@]}"; do
                        for random_turn in "${randamTrun[@]}"; do
                            for expand in "${expand_count[@]}"; do
                                output_file="${output_dir}/${executable}_tuple${tuple_value}_c${c}_boltzmann${boltzmann}_expectimax${expectimax}_depth${depth}_randomTurn${random_turn}_expand${expand}_seed${seed}.log"

                                # 実行とプロセス管理
                                ./"${executable}${tuple_value}" "$seed" "$game" "${tuple_value}tuple_data_9.dat" "$depth" "$random_turn" "$expand" "$debug" "$c" "$boltzmann" "$expectimax" >"$output_file" &
                                joblist+=($!) # バックグラウンドプロセスのPIDを記録
                                wait_for_jobs # プロセス数を制限
                                echo "Launched: "${executable}${tuple_value}" with seed=$seed, tuple=$tuple_value, c=$c, boltzmann=$boltzmann, expectimax=$expectimax, depth=$depth, randomTurn=$random_turn, expand=$expand"
                            done
                        done
                    done
                done
            done
        done
    done
done

# すべてのプロセスが終了するのを待つ
wait
echo "All jobs completed."
