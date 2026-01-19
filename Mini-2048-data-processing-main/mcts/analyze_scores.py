import os
import re
import sys
import statistics
import argparse
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


# 指定したディレクトリの平均スコアと中央値を計算
def calculate_scores(directory):
    results = []
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            subdir = os.path.join(root, dir_name)
            file_path = os.path.join(subdir, "after-state.txt")

            if os.path.isfile(file_path):
                scores = []
                with open(file_path, "r") as file:
                    for line in file:
                        match = re.search(
                            r"gameover_turn: \d+; game: \d+; progress: \d+; score: (\d+)",
                            line,
                        )
                        if match:
                            scores.append(int(match.group(1)))

                if scores:
                    avg_score = sum(scores) / len(scores)
                    median_score = statistics.median(scores)
                    # ディレクトリ名をパラメータとして抽出
                    params = extract_params(dir_name)
                    results.append({**params, "Average": avg_score, "Median": median_score})
    return results


# ディレクトリ名からパラメータを抽出
def extract_params(dir_name):
    match = re.search(
        r"simulations(\d+)_randomTurn(\d+)_expandcount(\d+)_c(-?\d+)_Boltzmann(\d+)_expectimax(\d+)",
        dir_name,
    )
    if match:
        return {
            "simulations": int(match.group(1)),
            "randomTurn": int(match.group(2)),
            "expandcount": int(match.group(3)),
            "c": int(match.group(4)),
            "Boltzmann": int(match.group(5)),
            "expectimax": int(match.group(6)),
        }
    else:
        return {}


# 相関を計算し、可視化
def calculate_and_visualize_correlation(df):
    # Pandasの出力を省略しない設定
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)

    # 相関行列を計算
    correlation = df.corr()

    # 相関行列を出力
    print("\nCorrelation Matrix:")
    print(correlation)

    # ヒートマップで可視化
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation, annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Correlation Matrix of Parameters")
    plt.show()



# メイン処理
def main():
    parser = argparse.ArgumentParser(description="Analyze scores and compute correlations.")
    parser.add_argument("subdir", type=str, help="Subdirectory under 'board_data'")
    args = parser.parse_args()

    default_base_directory = "../board_data/"  # デフォルトの基点ディレクトリ
    base_directory = os.path.join(default_base_directory, args.subdir)

    if not os.path.isdir(base_directory):
        print(f"Error: Directory '{base_directory}' does not exist.")
        sys.exit(1)

    # スコア計算
    results = calculate_scores(base_directory)

    if not results:
        print("No valid data found.")
        sys.exit(0)

    # データフレームに変換
    df = pd.DataFrame(results)

    # Boltzmann=1 の場合は c を除外
    df_filtered = df[df["Boltzmann"] == 1].drop(columns=["c"], errors="ignore")

    # 相関を計算して可視化
    print("Correlation for Boltzmann=1:")
    calculate_and_visualize_correlation(df_filtered)

    # Boltzmann=0 の場合も表示
    df_filtered_c = df[df["Boltzmann"] == 0]
    if not df_filtered_c.empty:
        print("Correlation for Boltzmann=0:")
        calculate_and_visualize_correlation(df_filtered_c)


if __name__ == "__main__":
    main()