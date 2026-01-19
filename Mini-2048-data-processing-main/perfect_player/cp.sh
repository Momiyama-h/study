#!/bin/bash

# コピー元とコピー先の基本ディレクトリ
SOURCE_DIR="../board_data/MCTS4"
DEST_DIR="../board_data"

# コピーしたいディレクトリ名のリスト
directories=(
    "game_count100_evfile4tuple_data_9.dat_simulations.*randomTurn0_expandcount50_c-1_Boltzmann0_expectimax*"
)

# ループでコピーを実行
for dir in "${directories[@]}"; do
    src="$SOURCE_DIR/$dir"
    dest="$DEST_DIR/$dir"

    if [ -d "$src" ]; then
        echo "Copying $src to $dest..."
        cp -r "$src" "$dest"
    else
        echo "Source directory $src does not exist. Skipping."
    fi
done
