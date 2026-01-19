import csv
import matplotlib.pyplot as plt
from collections import defaultdict
import argparse

# デフォルトのタイルパターン
DEFAULT_PATTERN = [0, 1, 2, 0, 0, 1, 0, 0, 0]

def parse_pattern(pattern_str):
    """カンマ区切りの文字列をint配列に変換"""
    try:
        pattern = [int(x.strip()) for x in pattern_str.split(',')]
        if len(pattern) != 9:
            raise ValueError(f"Pattern must have exactly 9 elements, got {len(pattern)}")
        return pattern
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid pattern format: {e}")

def count_pattern_matches(filepath, pattern):
    """CSVからパターン一致を1000ゲーム単位でカウント"""
    counts = defaultdict(int)  # {グループ番号: 出現回数}
    
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            game_id = int(row['game_id'])
            tiles = [int(row[f'tile{i}']) for i in range(9)]
            
            if tiles == pattern:
                group = (game_id - 1) // 1000  # 1-1000 → 0, 1001-2000 → 1, ...
                counts[group] += 1
    
    return counts

def plot_frequency(sym_csv, nosym_csv, pattern, output, games_per_group):
    """両CSVのパターン出現頻度を比較するグラフを作成"""
    
    print(f"Tracking pattern: {pattern}")
    print(f"Games per group: {games_per_group}")
    
    # カウント関数をグループサイズに対応させる
    def count_with_group_size(filepath, pattern, group_size):
        counts = defaultdict(int)
        with open(filepath, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                game_id = int(row['game_id'])
                tiles = [int(row[f'tile{i}']) for i in range(9)]
                
                if tiles == pattern:
                    group = (game_id - 1) // group_size
                    counts[group] += 1
        return counts
    
    # 各CSVからカウント
    sym_counts = count_with_group_size(sym_csv, pattern, games_per_group)
    nosym_counts = count_with_group_size(nosym_csv, pattern, games_per_group)
    
    # グループ番号の範囲を取得
    all_groups = set(sym_counts.keys()) | set(nosym_counts.keys())
    if not all_groups:
        print("No matches found in either file.")
        return
    
    max_group = max(all_groups)
    groups = list(range(max_group + 1))
    
    # 各グループの値を取得（存在しない場合は0）
    sym_values = [sym_counts.get(g, 0) for g in groups]
    nosym_values = [nosym_counts.get(g, 0) for g in groups]
    
    # X軸ラベル
    x_labels = [f"{g*games_per_group+1}-{(g+1)*games_per_group}" for g in groups]
    
    # グラフ作成
    plt.figure(figsize=(14, 6))
    plt.plot(groups, sym_values, 'b-o', label='Symmetric', markersize=4, alpha=0.7)
    plt.plot(groups, nosym_values, 'r-s', label='Non-symmetric', markersize=4, alpha=0.7)
    
    plt.xlabel('Game ID Range')
    plt.ylabel('Pattern Match Count')
    plt.title(f'Pattern {pattern} Frequency per {games_per_group} Games')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # X軸ラベルを間引いて表示
    step = max(1, len(groups) // 10)
    plt.xticks(groups[::step], x_labels[::step], rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    plt.close()
    
    print(f"Graph saved to: {output}")
    print(f"Sym total matches: {sum(sym_values)}")
    print(f"Notsym total matches: {sum(nosym_values)}")

def main():
    parser = argparse.ArgumentParser(
        description='Compare pattern frequency between sym and notsym board logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # デフォルトパターンを使用
  # prev: python pattern_frequency.py --sym board_log.csv --nosym board_log_nosym.csv
  python pattern_frequency.py --sym board_log.csv --nosym board_log_notsym.csv

  # カスタムパターンを指定
  python pattern_frequency.py --pattern "0,1,2,0,0,1,0,0,0"

  # 500ゲーム単位で集計
  python pattern_frequency.py --group-size 500

  # すべてのオプションを指定
  # prev: python pattern_frequency.py --sym board_log.csv --nosym board_log_nosym.csv \\
  python pattern_frequency.py --sym board_log.csv --nosym board_log_notsym.csv \\
      --pattern "1,1,0,0,0,0,0,0,0" --group-size 2000 --output custom_graph.png
        '''
    )
    
    parser.add_argument('--sym', default='board_log.csv',
                        help='Symmetric version CSV (default: board_log.csv)')
    # prev default: board_log_nosym.csv
    parser.add_argument('--nosym', default='board_log_notsym.csv',
                        help='Non-symmetric version CSV (default: board_log_notsym.csv)')
    parser.add_argument('--pattern', '-p', type=parse_pattern, default=None,
                        help='Tile pattern to track as comma-separated values (e.g., "0,1,2,0,0,1,0,0,0")')
    parser.add_argument('--group-size', '-g', type=int, default=1000,
                        help='Number of games per group (default: 1000)')
    parser.add_argument('--output', '-o', default='pattern_frequency.png',
                        help='Output PNG file (default: pattern_frequency.png)')
    
    args = parser.parse_args()
    
    # パターンが指定されていなければデフォルトを使用
    pattern = args.pattern if args.pattern is not None else DEFAULT_PATTERN
    
    plot_frequency(args.sym, args.nosym, pattern, args.output, args.group_size)

if __name__ == '__main__':
    main()
