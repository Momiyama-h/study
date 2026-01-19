import os
import re
import sys
import statistics
import glob
from collections import defaultdict

def read_progress_from_file(file_path):
    """ファイルからprogressの値を読み取る"""
    progress_values = []
    if os.path.isfile(file_path):
        with open(file_path, "r") as file:
            for line in file:
                match = re.search(
                    r"gameover_turn: \d+; game: \d+; progress: (\d+); score: \d+",
                    line,
                )
                if match:
                    progress_values.append(int(match.group(1)))
    return progress_values

def get_base_dirname(path):
    """seedの数字を除いたディレクトリ名を返す"""
    dirname = os.path.basename(path)
    return re.sub(r'_seed\d+$', '', dirname)

def calculate_progress(directory):
    """指定したディレクトリの平均progress、中央値、標準偏差を計算"""
    results = []
    file_path = os.path.join(directory, "after-state.txt")
    progress_values = read_progress_from_file(file_path)
    
    if progress_values:
        avg_progress = sum(progress_values) / len(progress_values)
        median_progress = statistics.median(progress_values)
        std_dev = statistics.stdev(progress_values) if len(progress_values) > 1 else 0
        base_name = get_base_dirname(directory)
        results.append((directory, base_name, avg_progress, median_progress, std_dev, progress_values))
    else:
        base_name = get_base_dirname(directory)
        results.append((directory, base_name, None, None, None, None))
    return results

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
        print("Error: Please specify a pattern (e.g., 'PP', 'NT4*', '*')")
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
        dir_results = calculate_progress(directory)
        all_results.extend(dir_results)

    # 結果をベース名でグループ化
    grouped_results = defaultdict(list)
    for path, base_name, avg, med, std, progress_values in all_results:
        if avg is not None:
            grouped_results[base_name].append((path, avg, med, std, progress_values))

    # グループごとに統計を計算
    final_results = []
    for base_name, group in grouped_results.items():
        all_progress = []
        for _, _, _, _, progress_values in group:
            all_progress.extend(progress_values)
        
        if all_progress:
            avg_progress = sum(all_progress) / len(all_progress)
            median_progress = statistics.median(all_progress)
            std_dev = statistics.stdev(all_progress) if len(all_progress) > 1 else 0
            final_results.append((base_name, avg_progress, median_progress, std_dev, len(all_progress)))

    # 結果をソート（平均progressの降順）
    sorted_results = sorted(final_results, key=lambda x: x[1], reverse=True)

    # 表示件数を調整
    if display_count == -1:
        display_count = len(sorted_results)

    # 結果を表示
    print("\nResults by Directory (grouped by base name):")
    print(f"{'Player':<30} {'Average':>10} {'Median':>10} {'Std Dev':>10} {'Games':>8}")
    print("-" * 72)
    
    for base_name, avg, med, std, count in sorted_results[:display_count]:
        print(f"{base_name:<30} {avg:>10.2f} {med:>10.2f} {std:>10.2f} {count:>8}")

    # progressがないディレクトリを表示
    no_progress_results = [path for path, _, avg, _, _, _ in all_results if avg is None]
    if no_progress_results:
        print("\nDirectories with No Valid Progress Data:")
        for path in no_progress_results:
            print(path)

if __name__ == "__main__":
    main()
