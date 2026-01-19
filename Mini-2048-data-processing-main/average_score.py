import os
import re
import sys
import statistics
import glob
from collections import defaultdict

def read_scores_from_file(file_path):
    scores = []
    if os.path.isfile(file_path):
        with open(file_path, "r") as file:
            for line in file:
                match = re.search(
                    r"gameover_turn: \d+; game: \d+; progress: \d+; score: (\d+)",
                    line,
                )
                if match:
                    scores.append(int(match.group(1)))
    return scores

def get_base_dirname(path):
    """seedの数字を除いたディレクトリ名を返す"""
    dirname = os.path.basename(path)
    return re.sub(r'_seed\d+$', '', dirname)

# 指定したディレクトリの平均スコア、中央値、標準偏差を計算
def calculate_scores(directory):
    results = []
    file_path = os.path.join(directory, "after-state.txt")
    scores = read_scores_from_file(file_path)
    
    if scores:
        avg_score = sum(scores) / len(scores)
        median_score = statistics.median(scores)
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
        base_name = get_base_dirname(directory)
        results.append((directory, base_name, avg_score, median_score, std_dev, scores))
    else:
        base_name = get_base_dirname(directory)
        results.append((directory, base_name, None, None, None, None))
    return results

# メイン処理
def main():
    default_base_directory = "board_data/"

    if len(sys.argv) > 1:
        # グロブパターンで一致するディレクトリを取得
        pattern = os.path.join(default_base_directory, sys.argv[1])
        matched_dirs = glob.glob(pattern)
        
        if not matched_dirs:
            print(f"Error: No directories match the pattern '{sys.argv[1]}'")
            sys.exit(1)
    else:
        print("Error: Please specify a pattern (e.g., 'EXP*')")
        sys.exit(1)

    # 表示件数を指定 (デフォルトは全件)
    if len(sys.argv) > 2:
        try:
            display_count = int(sys.argv[2])
        except ValueError:
            print("Error: Display count must be an integer.")
            sys.exit(1)
    else:
        display_count = -1

    # 各ディレクトリの結果を計算
    all_results = []
    for directory in matched_dirs:
        dir_results = calculate_scores(directory)
        all_results.extend(dir_results)

    # 結果をベース名でグループ化
    grouped_results = defaultdict(list)
    for path, base_name, avg, med, std, scores in all_results:
        if avg is not None:
            grouped_results[base_name].append((path, avg, med, std, scores))

    # グループごとに統計を計算
    final_results = []
    for base_name, group in grouped_results.items():
        all_scores = []
        for _, _, _, _, scores in group:
            all_scores.extend(scores)
        
        if all_scores:
            avg_score = sum(all_scores) / len(all_scores)
            median_score = statistics.median(all_scores)
            std_dev = statistics.stdev(all_scores) if len(all_scores) > 1 else 0
            final_results.append((base_name, avg_score, median_score, std_dev))

    # 結果をソート
    sorted_results = sorted(final_results, key=lambda x: x[1], reverse=True)

    # 表示件数を調整
    if display_count == -1:
        display_count = len(sorted_results)

    # 結果を表示
    print("\nResults by Directory (grouped by base name):")
    max_name_length = max(len(base_name) for base_name, _, _, _ in sorted_results[:display_count])
    
    for base_name, avg, med, std in sorted_results[:display_count]:
        print(f"{base_name:{max_name_length}}: Average={avg:.2f}, Median={med:.2f}, Std Dev={std:.2f}")

    # スコアがないディレクトリを表示（アンパック数を修正）
    no_score_results = [path for path, _, avg, _, _, _ in all_results if avg is None]
    if no_score_results:
        print("\nDirectories with No Valid Scores:")
        for path in no_score_results:
            print(path)

if __name__ == "__main__":
    main()
