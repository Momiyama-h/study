#!/bin/bash

# コンパイル用ディレクトリを作成
mkdir -p bin

# play_greedy のコンパイル
for i in 6; do
    g++ -DT${i} play/play_greedy.cpp -o bin/play_greedy_t${i}_normal -std=c++20 -mcmodel=large -O2 -lz
    g++ -DT${i} play/play_greedy_mini_0.cpp -o bin/play_greedy_t${i}_mini_0 -std=c++20 -mcmodel=large -O2 -lz
    g++ -DT${i} play/play_greedy_mini.cpp -o bin/play_greedy_t${i}_mini_1 -std=c++20 -mcmodel=large -O2 -lz
    g++ -DT${i} play/play_greedy_mini_2.cpp -o bin/play_greedy_t${i}_mini_2 -std=c++20 -mcmodel=large -O2 -lz
    g++ -DT${i} play/play_greedy_mini_3.cpp -o bin/play_greedy_t${i}_mini_3 -std=c++20 -mcmodel=large -O2 -lz
    # デバッグ版のコンパイル（-g -O0 フラグでデバッグシンボル付き）
    # g++ -DT${i} -g -O0 play/play_greedy_mini_3.cpp -o bin/play_greedy_t${i}_mini_3_debug -std=c++20 -mcmodel=large -lz
    # g++ -DT${i} -g -O0 play/play_greedy.cpp -o bin/play_greedy_t${i}_normal_debug -std=c++20 -mcmodel=large -lz
done

# # play_expectimax のコンパイル
# for i in {1..9}; do
#         g++ -DT$i play/play_expectimax.cpp -o bin/play_expectimax_t${i} -std=c++20 -mcmodel=large -O2 -lz
# done

echo "Compilation completed."
