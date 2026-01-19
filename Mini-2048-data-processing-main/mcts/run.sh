#!/bin/bash

# 最大同時実行プロセス数
max_jobs=16

# プロセス管理用
joblist=()

# 固定設定
seed=0
game=100
tuple=(4 6)
simu=(3 50 400 3000 15000 55000)
debug=0
<<<<<<< Updated upstream
randamTrun=(0 1 2)
=======
randamTrun=(0)
>>>>>>> Stashed changes
expand_count=(1 50)

# 可変パラメータ
boltzmann_values=(0 1)
expectimax_values=(0 1)

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

for tuple_value in "${tuple[@]}"; do
    for expectimax in "${expectimax_values[@]}"; do
        # expectimaxが1の場合、c_valuesを-1だけに制限
        if [ "$expectimax" -eq 1 ]; then
            c_values=(-1)
        else
            c_values=(-1 1000)
        fi

        for c in "${c_values[@]}"; do
            for boltzmann in "${boltzmann_values[@]}"; do
                for depth in "${simu[@]}"; do
                    for random_turn in "${randamTrun[@]}"; do
                        for expand in "${expand_count[@]}"; do
                            output_file="${output_dir}/${executable}_tuple${tuple_value}_c${c}_boltzmann${boltzmann}_expectimax${expectimax}_depth${depth}_randomTurn${random_turn}_expand${expand}.log"

                            # 実行とプロセス管理
                            ./"${executable}${tuple_value}" "$seed" "$game" "${tuple_value}tuple_data_9.dat" "$depth" "$random_turn" "$expand" "$debug" "$c" "$boltzmann" "$expectimax" >"$output_file" &
                            joblist+=($!) # バックグラウンドプロセスのPIDを記録
                            wait_for_jobs # プロセス数を制限
                            echo "Launched: "${executable}${tuple_value}" with tuple=$tuple_value, c=$c, boltzmann=$boltzmann, expectimax=$expectimax, depth=$depth, randomTurn=$random_turn, expand=$expand"
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
