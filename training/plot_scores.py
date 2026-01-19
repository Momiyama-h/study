import re
import matplotlib.pyplot as plt
import argparse
import os

def parse_scores(filepath):
    """
    .txtファイルからgame_idとscoreを抽出
    形式: "game <gameid> finished with score <score>"
    """
    pattern = re.compile(r'game\s+(\d+)\s+finished\s+with\s+score\s+(\d+)')
    scores = {}  # {game_id: score}
    
    print(f"Reading {filepath}...")
    with open(filepath, 'r') as f:
        for line in f:  # 1行ずつ読み込み（メモリ効率）
            match = pattern.search(line)
            if match:
                game_id = int(match.group(1))
                score = int(match.group(2))
                scores[game_id] = score
    
    print(f"  Found {len(scores)} games")
    return scores

def calculate_averages(scores, avescope):
    """
    avescope間隔でスコアの平均を計算
    """
    if not scores:
        return [], []
    
    max_game_id = max(scores.keys())
    x_values = []  # グループ終端のgame_id
    y_values = []  # 平均スコア
    
    current_sum = 0
    current_count = 0
    
    for game_id in range(1, max_game_id + 1):
        if game_id in scores:
            current_sum += scores[game_id]
            current_count += 1
        
        if game_id % avescope == 0:
            if current_count > 0:
                avg = current_sum / current_count
                x_values.append(game_id)
                y_values.append(avg)
            current_sum = 0
            current_count = 0
    
    return x_values, y_values

def plot_scores(file1, file2, avescope, output):
    """
    2つのファイルのスコア推移を比較するグラフを作成
    """
    # ファイル名から凡例名を生成
    label1 = os.path.splitext(os.path.basename(file1))[0]
    label2 = os.path.splitext(os.path.basename(file2))[0]
    
    # データ読み込み
    scores1 = parse_scores(file1)
    scores2 = parse_scores(file2)
    
    # 平均計算
    x1, y1 = calculate_averages(scores1, avescope)
    x2, y2 = calculate_averages(scores2, avescope)
    
    print(f"Plotting {len(x1)} points for {label1}")
    print(f"Plotting {len(x2)} points for {label2}")
    
    # グラフ作成
    plt.figure(figsize=(14, 6))
    plt.plot(x1, y1, 'b-', label=label1, linewidth=1.5, alpha=0.8)
    plt.plot(x2, y2, 'r-', label=label2, linewidth=1.5, alpha=0.8)
    
    plt.xlabel('Game ID')
    plt.ylabel(f'Average Score (per {avescope} games)')
    plt.title(f'Score Progression (averaged every {avescope} games)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output, dpi=150)
    plt.close()
    
    print(f"Graph saved to: {output}")
    
    # 統計情報
    if y1:
        print(f"{label1}: min={min(y1):.1f}, max={max(y1):.1f}, final={y1[-1]:.1f}")
    if y2:
        print(f"{label2}: min={min(y2):.1f}, max={max(y2):.1f}, final={y2[-1]:.1f}")

def main():
    parser = argparse.ArgumentParser(
        description='Plot average score progression from game log files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # 1000ゲーム単位で平均
  # prev: python plot_scores.py --file1 output_log.txt --file2 output_log_nosym.txt --avescope 1000
  python plot_scores.py --file1 output_log.txt --file2 output_log_notsym.txt --avescope 1000

  # 5000ゲーム単位で平均、出力ファイル名指定
  python plot_scores.py --file1 log1.txt --file2 log2.txt --avescope 5000 --output result.png
        '''
    )
    
    parser.add_argument('--file1', '-f1', required=True,
                        help='First log file (.txt)')
    parser.add_argument('--file2', '-f2', required=True,
                        help='Second log file (.txt)')
    parser.add_argument('--avescope', '-a', type=int, default=10000,
                        help='Averaging interval (default: 10000)')
    parser.add_argument('--output', '-o', default='score_progression.png',
                        help='Output PNG file (default: score_progression.png)')
    
    args = parser.parse_args()
    
    plot_scores(args.file1, args.file2, args.avescope, args.output)

if __name__ == '__main__':
    main()
