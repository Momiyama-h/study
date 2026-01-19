#!/bin/bash

# Multistaging0 を Multistaging2 に変更するスクリプト

echo "ファイル名のMultistaging変更を開始します..."

# NT6ディレクトリ内のファイル名修正
DIR="1-9_dat/NT6"

if [ -d "$DIR" ]; then
    echo "ディレクトリ $DIR を処理中..."
    
    # Multistaging0をMultistaging2に変更
    for file in "$DIR"/*Multistaging0*.zip; do
        if [ -f "$file" ]; then
            # 新しいファイル名を生成（Multistaging0 -> Multistaging2）
            new_file=$(echo "$file" | sed 's/Multistaging0/Multistaging2/g')
            
            echo "リネーム: $file -> $new_file"
            mv "$file" "$new_file"
        fi
    done
    
    echo "NT6ディレクトリの修正完了"
else
    echo "ディレクトリ $DIR が見つかりません"
fi

# 他のNTディレクトリも処理する場合
for nt_num in {1..9}; do
    NT_DIR="1-9_dat/NT${nt_num}"
    
    if [ -d "$NT_DIR" ]; then
        echo "ディレクトリ $NT_DIR を処理中..."
        
        for file in "$NT_DIR"/*Multistaging0*.zip; do
            if [ -f "$file" ]; then
                new_file=$(echo "$file" | sed 's/Multistaging0/Multistaging2/g')
                echo "リネーム: $file -> $new_file"
                mv "$file" "$new_file"
            fi
        done
        
        echo "NT${nt_num}ディレクトリの修正完了"
    fi
done

echo "すべてのファイル名修正が完了しました"

# 修正後のファイル一覧表示
echo ""
echo "修正後のファイル一覧:"
find 1-9_dat/ -name "*Multistaging2*.zip" 2>/dev/null | head -10

echo ""
echo "修正スクリプト実行完了"
