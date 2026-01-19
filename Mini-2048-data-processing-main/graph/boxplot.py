import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict

from .common import (
    EvalAndHandProgress,
    GraphData,
    PlotData,
    PlayerData,
    get_eval_and_hand_progress,
)


def create_boxplot_by_progress_range(
    player_data: PlayerData,
    min_progress: int = 0,
    max_progress: int = 250,
    bin_width: int = 10,
    output: Path = Path("output/boxplot.pdf"),
    is_show: bool = False,
):
    """
    progressの範囲でビンに分けて、評価値比率の箱ひげ図を作成する
    """
    # ファイルから評価値データを読み込み
    eval_and_hand_progress = get_eval_and_hand_progress(player_data.eval_file)

    # model_nameをconfigから取得（scatter.pyと同様）
    model_name = player_data.name
    model_label = player_data.get("label", model_name)

    # progressごとにデータを整理（指定範囲内のみ）
    progress_data = defaultdict(list)

    for eval_data in eval_and_hand_progress:
        # 指定範囲内のもののみを使用
        if min_progress <= eval_data.prg <= max_progress:
            # 評価値が有効なもの（-10000000000以下を除外）
            valid_evals = [eval for eval in eval_data.evals if eval > -10000000000]
            if len(valid_evals) >= 2:
                # 最大値と最小値の比率を計算
                max_val = max(valid_evals)
                min_val = min(valid_evals)
                if max_val != 0:
                    ratio = max_val - min_val
                    progress_data[eval_data.prg].append(ratio)

    # ビンに分ける
    if not progress_data:
        print(f"Progress範囲 {min_progress}-{max_progress} に有効なデータがありません")
        return None

    bins = []
    bin_labels = []
    bin_data = []

    for bin_start in range(min_progress, max_progress + 1, bin_width):
        bin_end = min(bin_start + bin_width - 1, max_progress)
        bin_ratios = []

        for progress in range(bin_start, bin_end + 1):
            if progress in progress_data:
                bin_ratios.extend(progress_data[progress])

        if bin_ratios:  # 空でないビンのみ追加
            bins.append((bin_start, bin_end))
            bin_labels.append(f"{bin_start}-{bin_end}")
            bin_data.append(bin_ratios)

    if not bin_data:
        print("ビンに有効なデータがありません")
        return None

    output_file = output.with_stem(f"{output.stem}_{model_label}_progress")
    # 箱ひげ図を作成
    plt.figure(figsize=(16, 8))
    plt.boxplot(bin_data, tick_labels=bin_labels)
    plt.xlabel("Progress Range")
    plt.ylabel("Evaluation Ratio (Min/Max)")
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file)

    if is_show:
        plt.show()
    else:
        plt.close()

    print(f"箱ひげ図を {output} に保存しました")
    print(f"Progress範囲: {min_progress}-{max_progress}, ビン幅: {bin_width}")
    print(f"ビン数: {len(bin_data)}")
    for i, (bin_range, data) in enumerate(zip(bins, bin_data)):
        mean_ratio = np.mean(data)
        std_ratio = np.std(data)
        median_ratio = np.median(data)
        print(
            f"ビン {bin_range[0]}-{bin_range[1]}: {len(data)} データポイント, 平均: {mean_ratio:.4f}, 中央値: {median_ratio:.4f}, 標準偏差: {std_ratio:.4f}"
        )

    return None


def create_boxplot_by_max_eval(
    player_data: PlayerData,
    num_bins: int = 10,
    output: Path = Path("output/boxplot_maxeval.pdf"),
    is_show: bool = False,
):
    """
    最大評価値を基準にビンに分けて、評価値比率の箱ひげ図を作成する
    """
    # ファイルから評価値データを読み込み
    eval_and_hand_progress = get_eval_and_hand_progress(player_data.eval_file)

    # model_nameをconfigから取得
    model_name = player_data.name
    model_label = player_data.get("label", model_name)

    # 有効なデータを抽出
    valid_data = []
    for eval_data in eval_and_hand_progress:
        # 評価値が有効なもの（-10000000000以下を除外）
        valid_evals = [eval for eval in eval_data.evals if eval > -10000000000]
        if len(valid_evals) >= 2:
            # 最大値と最小値の比率を計算
            max_val = max(valid_evals)
            min_val = min(valid_evals)
            if max_val != 0:
                ratio = max_val - min_val
                valid_data.append((max_val, ratio))

    if not valid_data:
        print("有効なデータがありません")
        return None

    # 最大評価値でソート
    valid_data.sort(key=lambda x: x[0])
    max_values = [x[0] for x in valid_data]
    ratios = [x[1] for x in valid_data]

    # 等間隔でビンに分ける
    min_val = min(max_values)
    max_val_range = max(max_values)
    bin_edges = np.linspace(min_val, max_val_range, num_bins + 1)

    bin_data = []
    bin_labels = []

    for i in range(num_bins):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i + 1]

        # このビンに含まれるデータを抽出
        bin_ratios = []
        for max_val, ratio in valid_data:
            if bin_start <= max_val <= bin_end:
                bin_ratios.append(ratio)

        if bin_ratios:  # 空でないビンのみ追加
            bin_data.append(bin_ratios)
            bin_labels.append(f"{bin_start:.0f}-{bin_end:.0f}")

    if not bin_data:
        print("ビンに有効なデータがありません")
        return None

    output_file = output.with_stem(f"{output.stem}_{model_label}_maxeval")
    # 箱ひげ図を作成
    plt.figure(figsize=(14, 8))
    plt.boxplot(bin_data, tick_labels=bin_labels)
    plt.xlabel("Max Evaluation Value Range")
    plt.ylabel("Evaluation Ratio (Min/Max)")
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file)

    if is_show:
        plt.show()
    else:
        plt.close()

    print(f"最大評価値基準の箱ひげ図を {output} に保存しました")
    print(f"ビン数: {len(bin_data)}")
    for i, (label, data) in enumerate(zip(bin_labels, bin_data)):
        mean_ratio = np.mean(data)
        std_ratio = np.std(data)
        median_ratio = np.median(data)
        print(
            f"ビン {label}: {len(data)} データポイント, 平均: {mean_ratio:.4f}, 中央値: {median_ratio:.4f}, 標準偏差: {std_ratio:.4f}"
        )

    return None


def plot_boxplot_eval_ratios(
    player_data_list: list[PlayerData],
    output: Path,
    is_show: bool = False,
    min_progress: int = 0,
    max_progress: int = 250,
    bin_width: int = 10,
):
    """
    評価値比率の箱ひげ図をプロットする
    scatter.pyと同様に、各ファイルに対して個別の箱ひげ図を作成する
    """
    for pd in sorted(player_data_list):
        create_boxplot_by_progress_range(
            player_data=pd,
            min_progress=min_progress,
            max_progress=max_progress,
            bin_width=bin_width,
            output=output,
            is_show=is_show,
        )
        create_boxplot_by_max_eval(
            player_data=pd,
            num_bins=10,
            output=output,
            is_show=is_show,
        )

    return None


if __name__ == "__main__":
    # テスト用の実行例
    player_eval_files = [Path("board_data/CNN_DEEP/eval.txt")]
    plot_boxplot_eval_ratios(
        player_eval_files=player_eval_files,
        output=Path("output/boxplot_test.pdf"),
        config={},
        is_show=True,
        min_progress=0,
        max_progress=250,
        bin_width=10,
    )
