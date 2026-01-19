#!/bin/bash
wait_for_process() {
    local pid=$1
    while ps -p $pid > /dev/null; do
        echo "プロセス${pid}の終了を待っています..."
        sleep 60  # 1分ごとにチェック
    done
    echo "プロセス${pid}が終了しました。処理を開始します。"
}

MAX_THREADS=32  # 最大並列数
SEED=1          # 初期シード値
GAMES=1000      # 実行するゲーム数
JOB_COUNT=0     # 現在の並列ジョブ数

# ログ保存ディレクトリ作成
mkdir -p play_logs

# NT1〜NT9までループ
for i in 6; do
    DIR="/home/matsu-lab/terauchi/Mini2048_NewTypeTuple/src/cpp/ntn_learn/NT${i}/dat/"  # zipファイルのディレクトリ
    PLAY_DIR="./bin"  # 実行ファイルのディレクトリ

    if [ $i -eq 7 ]; then
        echo "NT7: 実行中のジョブが8個になるまで待機します..." > /dev/null
        while [ "$JOB_COUNT" -gt 0 ]; do
            wait -n
            ((JOB_COUNT--))
        done
        MAX_THREADS=15
    fi
    if [ $i -eq 8 ]; then
        echo "NT8: 実行中のジョブが2個になるまで待機します..." > /dev/null
        while [ "$JOB_COUNT" -gt 0 ]; do
            wait -n
            ((JOB_COUNT--))
        done
        MAX_THREADS=3
    fi
    if [ $i -eq 9 ]; then
        echo "NT9: 実行中のジョブが1個になるまで待機します..." > /dev/null
        while [ "$JOB_COUNT" -gt 0 ]; do
            wait -n
            ((JOB_COUNT--))
        done
        MAX_THREADS=1
    fi

    # ディレクトリの存在確認
    if [ ! -d "$DIR" ]; then
        echo "スキップ: $DIR は存在しません"
        continue
    fi

    # すべてのzipファイルに対してループ
    for ZIP_FILE in $DIR/*.zip; do
        echo "実行中のzipファイル: $ZIP_FILE"
        if [ -f "$ZIP_FILE" ]; then
            LOG_FILE="play_logs/NT${i}_$(basename "$ZIP_FILE" .zip).log"
            echo $BASENAME
            
            # zipファイル名に応じて実行ファイルを決定
            BASENAME=$(basename "$ZIP_FILE")
            if [[ "$BASENAME" == *_mini0* ]]; then
                EXEC_FILE="$PLAY_DIR/play_greedy_t${i}_mini_0"
            elif [[ "$BASENAME" == *_mini1* ]]; then
                EXEC_FILE="$PLAY_DIR/play_greedy_t${i}_mini_1"
            elif [[ "$BASENAME" == *_mini2* ]]; then
                EXEC_FILE="$PLAY_DIR/play_greedy_t${i}_mini_2"
            elif [[ "$BASENAME" == *_mini3* ]]; then
                EXEC_FILE="$PLAY_DIR/play_greedy_t${i}_mini_3"
                # echo "実行中: $EXEC_FILE $SEED $GAMES $ZIP_FILE" | tee -a "$LOG_FILE"
            else
                EXEC_FILE="$PLAY_DIR/play_greedy_t${i}_normal"  # デフォルト
            fi
            
            echo "実行中: $EXEC_FILE $SEED $GAMES $ZIP_FILE" | tee -a "$LOG_FILE"
            $EXEC_FILE $SEED $GAMES $ZIP_FILE > "$LOG_FILE" &

            # スレッド管理
            ((JOB_COUNT++))
            if [ "$JOB_COUNT" -ge "$MAX_THREADS" ]; then
                wait -n
                ((JOB_COUNT--))
            fi
        fi
    done
done

# すべてのジョブの終了を待つ
wait